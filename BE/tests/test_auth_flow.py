"""Integration test against the local MySQL and RAG index configured in BE/.env."""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.chat import chat_service
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app


class AuthFlowTest(unittest.TestCase):
    def test_accounts_own_history_and_guests_do_not_persist(self) -> None:
        first_email = f"test-{uuid4().hex}@example.com"
        second_email = f"test-{uuid4().hex}@example.com"
        user_ids: list[int] = []
        try:
            with TestClient(app) as first, TestClient(app) as second, TestClient(app) as guest:
                response = first.post("/auth/register", json={"display_name": "Người tập A", "email": first_email, "password": "test-password-123"})
                self.assertEqual(response.status_code, 201, response.text)
                self.assertIn("httponly", response.headers["set-cookie"].lower())
                user_ids.append(response.json()["id"])
                self.assertEqual(first.get("/auth/me").json()["email"], first_email)

                answer = first.post("/chat", json={"message": "Gợi ý lịch tập 3 buổi/tuần"})
                self.assertEqual(answer.status_code, 200, answer.text)
                conversation_id = answer.json()["conversation_id"]
                self.assertIsNotNone(conversation_id)
                self.assertEqual(len(first.get("/conversations").json()), 1)
                self.assertEqual(len(first.get(f"/conversations/{conversation_id}").json()["messages"]), 2)

                chat_service.cache_clear()  # A new in-memory chatbot must rebuild context from MySQL.
                follow_up = first.post("/chat", json={"conversation_id": conversation_id, "message": "Còn 4 ngày thì sao?"})
                self.assertEqual(follow_up.status_code, 200, follow_up.text)
                self.assertIn("4 buổi/tuần", follow_up.json()["answer"])
                self.assertEqual(len(first.get(f"/conversations/{conversation_id}").json()["messages"]), 4)

                response = second.post("/auth/register", json={"display_name": "Người tập B", "email": second_email, "password": "test-password-456"})
                self.assertEqual(response.status_code, 201, response.text)
                user_ids.append(response.json()["id"])
                self.assertEqual(second.get(f"/conversations/{conversation_id}").status_code, 404)
                self.assertEqual(second.post("/chat", json={"conversation_id": conversation_id, "message": "Còn 4 ngày?"}).status_code, 404)

                self.assertEqual(guest.get("/conversations").status_code, 401)
                guest_answer = guest.post("/chat", json={"message": "Gợi ý lịch tập 2 buổi/tuần"})
                self.assertEqual(guest_answer.status_code, 200, guest_answer.text)
                self.assertIsNone(guest_answer.json()["conversation_id"])
                self.assertEqual(len(first.get("/conversations").json()), 1)

                self.assertEqual(first.post("/auth/logout").status_code, 200)
                self.assertEqual(first.get("/auth/me").status_code, 401)
        finally:
            with SessionLocal() as db:
                for user_id in user_ids:
                    user = db.get(User, user_id)
                    if user:
                        db.delete(user)
                db.commit()


if __name__ == "__main__":
    unittest.main()
