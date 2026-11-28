"""Hồi quy cho các lỗi nêu trong bản nhận xét đồ án (28/11/2026).

Chạy offline: SQLite trong bộ nhớ và chatbot giả, không cần MySQL hoặc Ollama.
"""

from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import LOGIN_LIMIT, limiter
from app.db.models import ChatMessage, ChatRequestRecord, Conversation, LoginSession, User
from app.db.session import Base, get_db, purge_stale_records, utc_now
from app.main import app
from app.services.chat import PLAN_CLARIFICATION
from app.services.knowledge import load_exercises, text_sha256
from app.services.plans import make_plan


class StubChat:
    def __init__(self):
        self.calls = 0

    def ask(self, message, session_id=None, history_override=None):
        self.calls += 1
        return {"session_id": session_id or "guest", "answer": f"Trả lời: {message}", "sources": [], "refused": False}


class ReviewFixHTTPTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:",
                                    connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

        def local_db():
            with self.sessions() as db:
                yield db

        self.previous_overrides = dict(app.dependency_overrides)
        app.dependency_overrides[get_db] = local_db
        self.bot = StubChat()
        self.patches = [patch("app.main.init_schema"),
                        patch("app.api.routes.chat.indexed_count", return_value=783),
                        patch("app.api.routes.chat.chat_service", return_value=self.bot),
                        patch.object(limiter, "enabled", True)]
        for item in self.patches:
            item.start()
        limiter.reset()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches):
            item.stop()
        limiter.reset()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)
        self.engine.dispose()

    def register(self, email="review@example.com"):
        response = self.client.post("/auth/register", json={"display_name": "Reviewer", "email": email, "password": "password123"})
        self.assertEqual(response.status_code, 201, response.text)
        return response

    def test_messages_keep_order_when_timestamps_tie(self):
        """RV-01: Tin nhắn cũ lưu cùng giây vẫn hiện câu hỏi trước câu trả lời sau khi tải lại."""
        self.register()
        with self.sessions() as db:
            user = db.scalar(select(User))
            db.add(Conversation(id="c-1", user_id=user.id, title="Cũ"))
            same_second = datetime(2026, 11, 28, 10, 0, 0)
            # Thêm assistant trước và dùng id khiến thứ tự theo id bị ngược.
            for turn in range(3):
                at = same_second + timedelta(seconds=turn)
                db.add(ChatMessage(id=f"0-{turn}", conversation_id="c-1", role="assistant", content=f"A{turn}", sources=[], created_at=at))
                db.add(ChatMessage(id=f"z-{turn}", conversation_id="c-1", role="user", content=f"Q{turn}", sources=[], created_at=at))
            db.commit()
        messages = self.client.get("/conversations/c-1").json()["messages"]
        self.assertEqual([item["content"] for item in messages], ["Q0", "A0", "Q1", "A1", "Q2", "A2"])

    def test_new_messages_are_stored_with_increasing_timestamps(self):
        """RV-02: Câu trả lời được ghi sau câu hỏi; lịch sử nhiều lượt giữ đúng thứ tự."""
        self.register()
        first = self.client.post("/chat", json={"message": "Câu 1 về tập gym"}).json()
        cid = first["conversation_id"]
        for index in range(2, 6):
            self.assertEqual(self.client.post("/chat", json={"message": f"Câu {index} về tập gym", "conversation_id": cid}).status_code, 200)
        messages = self.client.get(f"/conversations/{cid}").json()["messages"]
        self.assertEqual([item["role"] for item in messages], ["user", "assistant"] * 5)
        self.assertEqual(messages[0]["content"], "Câu 1 về tập gym")
        with self.sessions() as db:
            rows = db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == cid)).all()
            pairs = {}
            for row in rows:
                pairs.setdefault(row.content.removeprefix("Trả lời: "), {})[row.role] = row.created_at
            for times in pairs.values():
                self.assertLess(times["user"], times["assistant"])

    def test_model_error_details_are_not_exposed(self):
        """RV-03: Lỗi nội bộ của model không bị trả nguyên văn cho client."""
        with patch.object(self.bot, "ask", side_effect=RuntimeError("C:\\secret\\path token=abc")), \
                self.assertLogs("app.api.routes.chat", level="ERROR"):
            response = self.client.post("/chat", json={"message": "Tập gym"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)
        self.assertNotIn("token", response.text)
        self.assertIn("Ollama", response.json()["detail"])

    def test_stale_cookie_is_cleared_so_guest_chat_continues(self):
        """RV-04: Cookie hết hạn nhận 401 kèm lệnh xóa cookie; request tiếp theo chat khách được."""
        self.register()
        token = self.client.cookies.get("ai4gym_session")
        with self.sessions() as db:
            db.get(LoginSession, sha256(token.encode()).hexdigest()).expires_at = utc_now() - timedelta(seconds=1)
            db.commit()
        rejected = self.client.post("/chat", json={"message": "Tập gym"})
        self.assertEqual(rejected.status_code, 401)
        set_cookie = rejected.headers.get("set-cookie", "").lower()
        self.assertIn("ai4gym_session=", set_cookie)
        self.assertIn("max-age=0", set_cookie)
        self.assertIsNone(self.client.cookies.get("ai4gym_session"))
        guest = self.client.post("/chat", json={"message": "Tập gym"})
        self.assertEqual(guest.status_code, 200, guest.text)
        self.assertIsNone(guest.json()["conversation_id"])

    def test_login_is_rate_limited(self):
        """RV-05: Đăng nhập sai liên tục bị chặn 429 kèm Retry-After."""
        self.register()
        payload = {"email": "review@example.com", "password": "wrong-password"}
        for _ in range(LOGIN_LIMIT.max_requests):
            self.assertEqual(self.client.post("/auth/login", json=payload).status_code, 401)
        blocked = self.client.post("/auth/login", json=payload)
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked.headers)

    def test_login_password_has_max_length(self):
        """RV-06: Mật khẩu đăng nhập quá 128 ký tự bị từ chối trước khi băm."""
        response = self.client.post("/auth/login", json={"email": "review@example.com", "password": "x" * 129})
        self.assertEqual(response.status_code, 422)

    def test_retry_with_same_request_id_does_not_duplicate(self):
        """RV-07: Gửi lại cùng request_id (khi mạng lỗi) không tạo thêm tin nhắn hay gọi lại AI."""
        self.register()
        payload = {"message": "Lịch tập 3 buổi/tuần", "request_id": "6f1d1c2e-1b7a-4c1e-9d55-2a4d3e5f6a7b"}
        first = self.client.post("/chat", json=payload)
        second = self.client.post("/chat", json=payload)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(self.bot.calls, 1)
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(ChatMessage)), 2)


class ReviewFixUnitTest(unittest.TestCase):
    def test_stale_sessions_and_request_records_are_purged(self):
        """RV-08: Dọn phiên hết hạn và bản ghi request_id quá 24 giờ."""
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)
        with sessionmaker(bind=engine)() as db:
            user = User(email="purge@example.com", display_name="Purge", password_hash="x")
            db.add(user)
            db.flush()
            now = utc_now()
            db.add_all([
                LoginSession(token_hash="a" * 64, user_id=user.id, expires_at=now - timedelta(minutes=1)),
                LoginSession(token_hash="b" * 64, user_id=user.id, expires_at=now + timedelta(days=1)),
                ChatRequestRecord(user_id=user.id, request_id="old", message_hash="h", conversation_id="c",
                                  response_json={}, created_at=now - timedelta(days=2)),
                ChatRequestRecord(user_id=user.id, request_id="new", message_hash="h", conversation_id="c",
                                  response_json={}),
            ])
            db.commit()
            purge_stale_records(db)
            self.assertEqual(db.scalars(select(LoginSession.token_hash)).all(), ["b" * 64])
            self.assertEqual(db.scalars(select(ChatRequestRecord.request_id)).all(), ["new"])
        engine.dispose()

    def test_plan_wording_does_not_claim_acsm_standard(self):
        """RV-09: Không gọi lịch mẫu là "chuẩn ACSM"."""
        self.assertNotIn("chuẩn ACSM", PLAN_CLARIFICATION)
        self.assertIn("tham khảo", PLAN_CLARIFICATION)

    def test_bodyweight_pull_day_is_labelled_honestly(self):
        """RV-10: Không dụng cụ thì buổi "Kéo" được đổi tên và có hướng dẫn bổ sung bài chèo."""
        plan = make_plan(days=6, equipment="home_bodyweight")
        pull_days = [day for day in plan["schedule"] if day["focus"].startswith("Kéo")]
        self.assertEqual(len(pull_days), 2)
        for day in pull_days:
            self.assertIn("Core & chuỗi sau", day["focus"])
        self.assertIn("chèo (row)", plan["guidance"])
        gym_plan = make_plan(days=6)
        self.assertNotIn("chèo (row)", gym_plan["guidance"])

    def test_exercise_source_links_are_unique(self):
        """RV-11: Mỗi bài tập trỏ tới một trang ACE riêng."""
        sources = [exercise["source"] for exercise in load_exercises()]
        self.assertEqual(len(sources), len(set(sources)))

    def test_text_hash_is_line_ending_independent(self):
        """RV-12: Hash tập test không đổi giữa LF (Linux) và CRLF (Windows)."""
        with tempfile.TemporaryDirectory() as folder:
            lf, crlf = Path(folder) / "lf.json", Path(folder) / "crlf.json"
            lf.write_bytes(b'[\n  "a"\n]')
            crlf.write_bytes(b'[\r\n  "a"\r\n]')
            self.assertEqual(text_sha256(lf), text_sha256(crlf))


if __name__ == "__main__":
    unittest.main()
