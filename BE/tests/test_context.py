import threading
import unittest

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from app.services.chat import ChatService, PROMPT


class FakeStore:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.document = Document(id="qa-test", page_content="Bài tập tạ tác động vào cơ bắp.", metadata={"title": "Bài tập tạ", "source": "test"})

    def similarity_search_with_relevance_scores(self, query: str, k: int):
        self.queries.append(query)
        return [(self.document, 0.9)]


class FakeChain:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def invoke(self, payload: dict) -> str:
        self.calls.append(payload)
        return "Câu trả lời từ tài liệu."


class ContextTest(unittest.TestCase):
    def make_service(self) -> tuple[ChatService, FakeStore, FakeChain]:
        service = ChatService.__new__(ChatService)
        store = FakeStore()
        chain = FakeChain()
        service.store = store
        service.chain = chain
        service.exercises = []
        service.exercise_docs = {}
        service.sessions = {}
        service.lock = threading.Lock()
        return service, store, chain

    def test_guest_uses_three_previous_turns_for_follow_up(self) -> None:
        service, store, chain = self.make_service()
        for turn in range(1, 5):
            service.ask(f"Cách tập tạ lượt {turn}", session_id="guest")

        response = service.ask("Nó tác động cơ nào?", session_id="guest")

        self.assertFalse(response["refused"])
        self.assertEqual(len(chain.calls[-1]["history"]), 6)
        self.assertEqual(chain.calls[-1]["history"][0], ("human", "Cách tập tạ lượt 2"))
        self.assertEqual(chain.calls[-1]["history"][-1], ("ai", "Câu trả lời từ tài liệu."))
        self.assertIn("Cách tập tạ lượt 2", store.queries[-1])
        self.assertIn("Cách tập tạ lượt 4", store.queries[-1])
        self.assertNotIn("Cách tập tạ lượt 1", store.queries[-1])

        messages = PROMPT.format_messages(**chain.calls[-1])
        self.assertIsInstance(messages[1], HumanMessage)
        self.assertIsInstance(messages[2], AIMessage)
        self.assertIsInstance(messages[-1], HumanMessage)

    def test_saved_history_is_trimmed_before_model_call(self) -> None:
        service, _, chain = self.make_service()
        saved = [
            {"role": role, "text": f"Lượt {turn} {role}"}
            for turn in range(1, 5)
            for role in ("user", "assistant")
        ]

        service.ask("Cách tập tạ?", session_id="account", history_override=saved)

        self.assertEqual(len(chain.calls[-1]["history"]), 6)
        self.assertEqual(chain.calls[-1]["history"][0], ("human", "Lượt 2 user"))

    def test_first_exercise_follow_up_resolves_from_plan(self) -> None:
        service, store, chain = self.make_service()
        service.exercises = [{"id": "bodyweight-squat", "name": "Squat trọng lượng cơ thể", "aliases": ["squat"]}]
        service.exercise_docs = {
            "exercise-bodyweight-squat": Document(
                id="exercise-bodyweight-squat",
                page_content="Squat trọng lượng cơ thể: đứng hai chân rộng bằng vai rồi hạ hông.",
                metadata={"title": "Squat trọng lượng cơ thể", "source": "test"},
            )
        }
        history = [
            {"role": "user", "text": "Gợi ý lịch tập 3 buổi/tuần"},
            {"role": "assistant", "text": "Lịch 3 buổi/tuần: Thứ Hai — Squat trọng lượng cơ thể, chống đẩy."},
        ]

        response = service.ask("Bài đầu tiên tập như thế nào?", history_override=history)

        self.assertFalse(response["refused"])
        self.assertEqual(response["sources"][0]["id"], "exercise-bodyweight-squat")
        self.assertIn("Squat trọng lượng cơ thể", store.queries[-1])
        self.assertIn("Squat trọng lượng cơ thể", chain.calls[-1]["question"])


if __name__ == "__main__":
    unittest.main()
