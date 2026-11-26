"""Bộ kiểm thử phần mềm mở rộng (Extended Software Acceptance Test Suite).

Thiết kế theo các kỹ thuật kiểm thử phần mềm chuẩn hóa:
- Phân tích giá trị biên (Boundary Value Analysis - BVA): TC-BVA-01 đến TC-BVA-05
- Phân vùng tương đương (Equivalence Partitioning - EP): TC-EP-01 đến TC-EP-05
- Bảng quyết định (Decision Table - DT): TC-DT-01 đến TC-DT-05
- Chuyển trạng thái & An toàn (State Transition & Security - ST/SEC): TC-ST-01 đến TC-SEC-03

Toàn bộ các ca kiểm thử chạy độc lập trên SQLite in-memory và stub bot, đảm bảo thực thi nhanh và an toàn.
"""

import unittest
from unittest.mock import patch
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import ChatMessage, Conversation
from app.db.session import Base, get_db
from app.main import app
from app.services.knowledge import load_exercises
from app.services.plans import make_plan


class StubChat:
    """Mock ChatService phục vụ kiểm thử phần mềm độc lập với Ollama."""

    def __init__(self):
        self.calls = []

    def ask(self, message: str, session_id: str | None = None, history_override: list | None = None) -> dict:
        self.calls.append((message, session_id, history_override))
        return {
            "session_id": session_id or "guest-test",
            "answer": f"Phản hồi mẫu cho: {message[:30]}",
            "sources": [{"id": "bodyweight-squat", "name": "Bodyweight Squat", "source": "https://acefitness.org"}],
            "refused": False,
        }


class ExtendedSoftwareAcceptanceTest(unittest.TestCase):
    """Bộ 20 ca kiểm thử phần mềm chuẩn hóa theo BVA, EP, Decision Table, State & Security."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

        def local_db():
            with self.sessions() as db:
                yield db

        self.previous_overrides = dict(app.dependency_overrides)
        app.dependency_overrides[get_db] = local_db
        self.bot = StubChat()
        self.patches = [
            patch("app.main.init_schema"),
            patch("app.api.routes.chat.indexed_count", return_value=783),
            patch("app.api.routes.chat.chat_service", return_value=self.bot),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches):
            item.stop()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)
        self.engine.dispose()

    def register_user(self, email: str = "tester@example.com", display_name: str = "Kiểm Thử Viên", password: str = "password123"):
        return self.client.post(
            "/auth/register",
            json={"display_name": display_name, "email": email, "password": password},
        )

    # =========================================================================
    # NHÓM 1: PHÂN TÍCH GIÁ TRỊ BIÊN (BOUNDARY VALUE ANALYSIS - BVA)
    # =========================================================================

    def test_bva_plans_valid_boundaries(self):
        """TC-BVA-01: Biên số ngày tạo lịch days=1 (min) và days=6 (max)."""
        valid_ids = {row["id"] for row in load_exercises()}

        # Biên dưới: days=1
        resp_min = self.client.get("/plans", params={"days": 1})
        self.assertEqual(resp_min.status_code, 200)
        data_min = resp_min.json()
        self.assertEqual(data_min["days_per_week"], 1)
        self.assertEqual(len(data_min["schedule"]), 1)
        self.assertIn("Toàn thân", data_min["split"])
        for day in data_min["schedule"]:
            self.assertTrue(day["exercises"])
            self.assertTrue({ex["id"] for ex in day["exercises"]}.issubset(valid_ids))

        # Biên trên: days=6
        resp_max = self.client.get("/plans", params={"days": 6})
        self.assertEqual(resp_max.status_code, 200)
        data_max = resp_max.json()
        self.assertEqual(data_max["days_per_week"], 6)
        self.assertEqual(len(data_max["schedule"]), 6)
        self.assertEqual(data_max["split"], "Push/Pull/Legs")
        for day in data_max["schedule"]:
            self.assertTrue(day["exercises"])
            self.assertTrue({ex["id"] for ex in day["exercises"]}.issubset(valid_ids))

    def test_bva_plans_invalid_boundaries(self):
        """TC-BVA-02: Biên vượt ngưỡng số ngày days=0, days=7, days=-1, days=100 trả về 422."""
        for invalid_days in [0, 7, -1, 100]:
            with self.subTest(days=invalid_days):
                response = self.client.get("/plans", params={"days": invalid_days})
                self.assertEqual(response.status_code, 422)

    def test_bva_chat_message_length_boundaries(self):
        """TC-BVA-03: Biên độ dài message chat: 1 ký tự (422), 2 ký tự (200), 1000 ký tự (200), 1001 ký tự (422)."""
        # Sát dưới biên hợp lệ (1 ký tự -> 422)
        resp_1 = self.client.post("/chat", json={"message": "a"})
        self.assertEqual(resp_1.status_code, 422)

        # Biên dưới hợp lệ (2 ký tự -> 200)
        resp_2 = self.client.post("/chat", json={"message": "cơ"})
        self.assertEqual(resp_2.status_code, 200)

        # Biên trên hợp lệ (1000 ký tự -> 200)
        resp_1000 = self.client.post("/chat", json={"message": "x" * 1000})
        self.assertEqual(resp_1000.status_code, 200)

        # Vượt biên trên hợp lệ (1001 ký tự -> 422)
        resp_1001 = self.client.post("/chat", json={"message": "x" * 1001})
        self.assertEqual(resp_1001.status_code, 422)

    def test_bva_register_display_name_boundaries(self):
        """TC-BVA-04: Biên độ dài tên hiển thị khi đăng ký: 1 ký tự (422), 2 ký tự (201), 80 ký tự (201), 81 ký tự (422)."""
        # 1 ký tự -> 422 (min_length=2)
        r1 = self.register_user(email="t1@example.com", display_name="A")
        self.assertEqual(r1.status_code, 422)

        # 2 ký tự -> 201
        r2 = self.register_user(email="t2@example.com", display_name="An")
        self.assertEqual(r2.status_code, 201)

        # 80 ký tự -> 201 (max_length=80)
        r80 = self.register_user(email="t80@example.com", display_name="B" * 80)
        self.assertEqual(r80.status_code, 201)

        # 81 ký tự -> 422
        r81 = self.register_user(email="t81@example.com", display_name="B" * 81)
        self.assertEqual(r81.status_code, 422)

    def test_bva_register_password_length_boundaries(self):
        """TC-BVA-05: Biên độ dài mật khẩu: 7 ký tự (422), 8 ký tự (201), 128 ký tự (201), 129 ký tự (422)."""
        # 7 ký tự -> 422
        rp7 = self.register_user(email="p7@example.com", password="P" * 7)
        self.assertEqual(rp7.status_code, 422)

        # 8 ký tự -> 201
        rp8 = self.register_user(email="p8@example.com", password="P" * 8)
        self.assertEqual(rp8.status_code, 201)

        # 128 ký tự -> 201
        rp128 = self.register_user(email="p128@example.com", password="P" * 128)
        self.assertEqual(rp128.status_code, 201)

        # 129 ký tự -> 422
        rp129 = self.register_user(email="p129@example.com", password="P" * 129)
        self.assertEqual(rp129.status_code, 422)

    # =========================================================================
    # NHÓM 2: PHÂN VÙNG TƯƠNG ĐƯƠNG (EQUIVALENCE PARTITIONING - EP)
    # =========================================================================

    def test_ep_exercises_valid_muscles(self):
        """TC-EP-01: Phân vùng nhóm cơ hợp lệ ('ngực', 'lưng', 'chân', 'vai', 'tay') đều trả danh mục chuẩn."""
        valid_muscles = ["ngực", "lưng", "chân", "vai", "tay"]
        for muscle in valid_muscles:
            with self.subTest(muscle=muscle):
                response = self.client.get("/exercises", params={"muscle": muscle})
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertGreater(len(data), 0, f"Nhóm cơ {muscle} phải có ít nhất 1 bài tập")

    def test_ep_exercises_case_insensitive_and_diacritics(self):
        """TC-EP-02: Phân vùng chuẩn hóa: viết hoa, khoảng trắng thừa, không dấu ('  NGỰC  ', 'nguc') đều tìm thấy kết quả."""
        base_res = self.client.get("/exercises", params={"muscle": "ngực"}).json()
        untrimmed_res = self.client.get("/exercises", params={"muscle": "  NGỰC  "}).json()
        no_accent_res = self.client.get("/exercises", params={"muscle": "nguc"}).json()

        self.assertGreater(len(base_res), 0)
        self.assertEqual(len(untrimmed_res), len(base_res))
        self.assertEqual(len(no_accent_res), len(base_res))
        base_ids = {x["id"] for x in base_res}
        self.assertEqual({x["id"] for x in untrimmed_res}, base_ids)
        self.assertEqual({x["id"] for x in no_accent_res}, base_ids)

    def test_ep_exercises_non_existent_muscle(self):
        """TC-EP-03: Phân vùng nhóm cơ không tồn tại ('dau_long', 'tim', '12345') trả về mảng rỗng [] và 200 OK."""
        for invalid_muscle in ["dau_long", "tim", "12345", "unknown_group"]:
            with self.subTest(muscle=invalid_muscle):
                response = self.client.get("/exercises", params={"muscle": invalid_muscle})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [])

    def test_ep_register_email_partitions(self):
        """TC-EP-04: Phân vùng định dạng email: hợp lệ (subdomain, dấu cộng) thành công; không hợp lệ bị từ chối 422."""
        valid_emails = ["user.test+1@domain.com.vn", "student_123@hcm.edu.vn"]
        for idx, email in enumerate(valid_emails):
            with self.subTest(valid_email=email):
                resp = self.register_user(email=email, display_name=f"User {idx}")
                self.assertEqual(resp.status_code, 201)

        invalid_emails = ["user@", "@domain.com", "plainaddress", "user space@domain.com"]
        for email in invalid_emails:
            with self.subTest(invalid_email=email):
                resp = self.register_user(email=email, display_name="User Invalid")
                self.assertEqual(resp.status_code, 422)

    def test_ep_utf8_and_emoji_support(self):
        """TC-EP-05: Phân vùng ký tự đặc biệt: Hỗ trợ tiếng Việt đầy đủ dấu và Emoji trong tên tài khoản và tin nhắn."""
        special_name = "Nguyễn Văn Tập Gym 💪🏋️"
        reg_resp = self.register_user(email="emoji@example.com", display_name=special_name)
        self.assertEqual(reg_resp.status_code, 201)
        self.assertEqual(reg_resp.json()["display_name"], special_name)

        me_resp = self.client.get("/auth/me")
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["display_name"], special_name)

        emoji_msg = "Tập squat thế nào cho đùi khỏe? 🔥💪"
        chat_resp = self.client.post("/chat", json={"message": emoji_msg})
        self.assertEqual(chat_resp.status_code, 200)
        conv_id = chat_resp.json()["conversation_id"]

        detail_resp = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["messages"][0]["content"], emoji_msg)

    # =========================================================================
    # NHÓM 3: BẢNG QUYẾT ĐỊNH (DECISION TABLE - DT)
    # =========================================================================

    def test_dt_bodyweight_hypertrophy_knee_limitation(self):
        """TC-DT-01: Quyết định: Không dụng cụ + Tăng cơ + Đau gối -> Loại bỏ squat/đạp chân, chỉ dùng bài bodyweight & thêm lời khuyên."""
        exercises_by_id = {ex["id"]: ex for ex in load_exercises()}
        plan = make_plan(days=3, equipment="home_bodyweight", goal="tang_co", limitations=["knee"])
        self.assertIn("Tại nhà - Không dụng cụ", plan["split"])
        self.assertIn("quá tải tiến triển", plan["guidance"])
        self.assertIn("Lưu ý khớp gối", plan["guidance"])

        all_exercise_ids = {
            exercise["id"]
            for day in plan["schedule"]
            for exercise in day["exercises"]
        }
        self.assertNotIn("bodyweight-squat", all_exercise_ids)
        self.assertNotIn("leg-press", all_exercise_ids)
        self.assertIn("glute-bridge", all_exercise_ids)
        for ex_id in all_exercise_ids:
            self.assertEqual(exercises_by_id[ex_id]["equipment"], "Không cần dụng cụ")

    def test_dt_dumbbell_fatloss(self):
        """TC-DT-02: Quyết định: Tạ đơn + Giảm mỡ -> Thay bài máy bằng tạ đơn (bent-over-row), hướng dẫn 150 phút aerobic."""
        exercises_by_id = {ex["id"]: ex for ex in load_exercises()}
        plan = make_plan(days=3, equipment="home_dumbbell", goal="giam_mo")
        self.assertIn("Tại nhà - Tạ đơn", plan["split"])
        self.assertIn("150 phút", plan["guidance"])

        all_exercise_ids = {
            exercise["id"]
            for day in plan["schedule"]
            for exercise in day["exercises"]
        }
        self.assertNotIn("lat-pulldown", all_exercise_ids)
        self.assertIn("bent-over-row", all_exercise_ids)
        for ex_id in all_exercise_ids:
            self.assertIn(exercises_by_id[ex_id]["equipment"], ("Không cần dụng cụ", "Ghế tập và tạ đơn"))

    def test_dt_gym_dual_limitations_knee_and_back(self):
        """TC-DT-03: Quyết định: Phòng Gym + Đa chấn thương (đau gối AND đau lưng dưới) -> Loại bỏ đồng thời cả 4 bài rủi ro."""
        plan = make_plan(days=4, equipment=None, limitations=["knee", "lower_back"])
        self.assertIn("Lưu ý khớp gối", plan["guidance"])
        self.assertIn("Lưu ý lưng dưới", plan["guidance"])

        all_exercise_ids = {
            exercise["id"]
            for day in plan["schedule"]
            for exercise in day["exercises"]
        }
        self.assertNotIn("bodyweight-squat", all_exercise_ids)
        self.assertNotIn("leg-press", all_exercise_ids)
        self.assertNotIn("seated-row", all_exercise_ids)
        self.assertNotIn("bent-over-row", all_exercise_ids)

    def test_dt_equipment_muscle_focus_isolation(self):
        """TC-DT-04: Quyết định: Tập trung nhóm cơ chân + Không dụng cụ -> Mọi ngày tập đều tập trung chân và chỉ dùng bodyweight."""
        exercises_by_id = {ex["id"]: ex for ex in load_exercises()}
        plan = make_plan(days=2, equipment="home_bodyweight", target_muscle="chan")
        for day in plan["schedule"]:
            self.assertIn("(Chân)", day["focus"])
            day_ex_ids = {ex["id"] for ex in day["exercises"]}
            self.assertNotIn("leg-press", day_ex_ids)
            self.assertIn("glute-bridge", day_ex_ids)
            for ex_id in day_ex_ids:
                self.assertEqual(exercises_by_id[ex_id]["equipment"], "Không cần dụng cụ")

    def test_dt_plan_push_pull_balance(self):
        """TC-DT-05: Quyết định: Lịch 6 buổi Push/Pull/Legs -> Đảm bảo chu kỳ Đẩy-Kéo-Chân lặp lại 2 lần, đủ 6 ngày."""
        plan = make_plan(days=6)
        self.assertEqual(plan["days_per_week"], 6)
        foci = [day["focus"] for day in plan["schedule"]]
        self.assertEqual(foci, ["Đẩy", "Kéo", "Chân", "Đẩy", "Kéo", "Chân"])
        self.assertEqual(len(plan["schedule"]), 6)

    # =========================================================================
    # NHÓM 4: CHUYỂN TRẠNG THÁI & AN TOÀN (STATE TRANSITION & SECURITY)
    # =========================================================================

    def test_st_conversation_full_lifecycle(self):
        """TC-ST-01: Chuyển trạng thái hội thoại: Tạo mới -> Chat -> Đổi tên -> Kiểm tra danh sách & chi tiết -> Xóa hội thoại và tin nhắn."""
        self.register_user(email="lifecycle@example.com")

        # 1. Tạo hội thoại qua POST /chat
        chat_resp = self.client.post("/chat", json={"message": "Xin chào bot gym"})
        self.assertEqual(chat_resp.status_code, 200)
        conv_id = chat_resp.json()["conversation_id"]
        self.assertIsNotNone(conv_id)

        # 2. Đổi tên hội thoại
        new_title = "Lịch tập ngực tháng 11"
        rename_resp = self.client.patch(f"/conversations/{conv_id}", json={"title": new_title})
        self.assertEqual(rename_resp.status_code, 200)
        self.assertEqual(rename_resp.json()["title"], new_title)

        # 3. Kiểm tra danh sách & chi tiết hội thoại
        list_resp = self.client.get("/conversations")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json()), 1)
        self.assertEqual(list_resp.json()[0]["title"], new_title)

        detail_resp = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["title"], new_title)
        self.assertEqual(len(detail_resp.json()["messages"]), 2)

        # 4. Xóa hội thoại (API REST trả về 204 No Content hoặc 200 OK)
        del_resp = self.client.delete(f"/conversations/{conv_id}")
        self.assertIn(del_resp.status_code, (200, 204))

        # 5. Xác nhận không còn hội thoại và tin nhắn trong database
        self.assertEqual(self.client.get("/conversations").json(), [])
        self.assertEqual(self.client.get(f"/conversations/{conv_id}").status_code, 404)
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Conversation)), 0)
            self.assertEqual(db.scalar(select(func.count()).select_from(ChatMessage)), 0)

    def test_st_guest_to_registered_transition(self):
        """TC-ST-02: Chuyển trạng thái khách sang thành viên: Khách không lưu DB -> Đăng ký lưu DB độc lập, không rò rỉ phiên."""
        guest_resp = self.client.post("/chat", json={"message": "Khách hỏi tư vấn"})
        self.assertEqual(guest_resp.status_code, 200)
        self.assertIsNone(guest_resp.json()["conversation_id"])

        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Conversation)), 0)
            self.assertEqual(db.scalar(select(func.count()).select_from(ChatMessage)), 0)

        self.register_user(email="member@example.com")
        member_resp = self.client.post("/chat", json={"message": "Thành viên hỏi lịch"})
        self.assertEqual(member_resp.status_code, 200)
        self.assertIsNotNone(member_resp.json()["conversation_id"])

        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Conversation)), 1)
            self.assertEqual(db.scalar(select(func.count()).select_from(ChatMessage)), 2)

    def test_sec_xss_sanitization_and_handling(self):
        """TC-SEC-01: An toàn XSS: Nhập payload <script> hoặc <img> vào tên, tin nhắn, tiêu đề -> Không gây lỗi 500, lưu trữ an toàn."""
        xss_payload = "<script>alert('XSS')</script><img src=x onerror=alert(1)>"
        reg_resp = self.register_user(email="xss@example.com", display_name=xss_payload)
        self.assertEqual(reg_resp.status_code, 201)
        self.assertEqual(reg_resp.json()["display_name"], xss_payload)

        me_resp = self.client.get("/auth/me")
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["display_name"], xss_payload)

        chat_resp = self.client.post("/chat", json={"message": xss_payload})
        self.assertEqual(chat_resp.status_code, 200)
        conv_id = chat_resp.json()["conversation_id"]

        rename_resp = self.client.patch(f"/conversations/{conv_id}", json={"title": "<b>Test</b>"})
        self.assertEqual(rename_resp.status_code, 200)

        detail_resp = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["title"], "<b>Test</b>")
        self.assertEqual(detail_resp.json()["messages"][0]["content"], xss_payload)

    def test_sec_idor_cross_account_isolation(self):
        """TC-SEC-02: Kiểm soát truy cập ngang (IDOR): Tài khoản B không thể đọc, sửa, xóa hoặc chat ké vào hội thoại của Tài khoản A."""
        self.register_user(email="user_a@example.com")
        chat_a = self.client.post("/chat", json={"message": "Hội thoại bí mật của A"})
        conv_a_id = chat_a.json()["conversation_id"]

        client_b = TestClient(app)
        client_b.__enter__()
        try:
            client_b.post(
                "/auth/register",
                json={"display_name": "Người dùng B", "email": "user_b@example.com", "password": "password123"},
            )
            self.assertEqual(client_b.get(f"/conversations/{conv_a_id}").status_code, 404)
            self.assertEqual(client_b.patch(f"/conversations/{conv_a_id}", json={"title": "B đổi tên"}).status_code, 404)
            self.assertEqual(client_b.delete(f"/conversations/{conv_a_id}").status_code, 404)
            self.assertEqual(client_b.post("/chat", json={"message": "B chat vào A", "conversation_id": conv_a_id}).status_code, 404)
        finally:
            client_b.__exit__(None, None, None)

        # Kiểm tra tài nguyên của User A vẫn nguyên vẹn
        detail_a = self.client.get(f"/conversations/{conv_a_id}")
        self.assertEqual(detail_a.status_code, 200)
        self.assertEqual(len(detail_a.json()["messages"]), 2)

    def test_sec_request_replay_protection(self):
        """TC-SEC-03: Chống replay attack: Gửi lặp cùng request_id trả về bản ghi cũ; đổi payload nhận 409 Conflict."""
        self.register_user(email="replay@example.com")
        req_id = str(uuid.uuid4())
        msg = "Câu hỏi lần một"

        resp1 = self.client.post("/chat", json={"message": msg, "request_id": req_id})
        self.assertEqual(resp1.status_code, 200)
        bot_call_count_before = len(self.bot.calls)

        resp2 = self.client.post("/chat", json={"message": msg, "request_id": req_id})
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json(), resp1.json())
        self.assertEqual(len(self.bot.calls), bot_call_count_before, "Không được gọi lại AI khi request_id bị lặp")

        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(ChatMessage)), 2)

        resp3 = self.client.post("/chat", json={"message": "Câu hỏi bị giả mạo", "request_id": req_id})
        self.assertEqual(resp3.status_code, 409)


if __name__ == "__main__":
    unittest.main()
