import unittest

from app.services.scope import in_scope, mentioned_muscles


class ScopeTest(unittest.TestCase):
    def test_everyday_gym_questions_are_in_scope(self) -> None:
        for question in (
            "cách tập cho vai to",
            "tập tay nên tập mấy rep 1 set",
            "vai to nên tập bài nào",
            "mấy set cho tay là đủ?",
        ):
            with self.subTest(question=question):
                self.assertTrue(in_scope(question))

    def test_non_gym_questions_stay_out_of_scope(self) -> None:
        for question in ("Vai trò của học tập là gì?", "Nấu món gì tối nay?", "Set trong Python là gì?"):
            with self.subTest(question=question):
                self.assertFalse(in_scope(question))

    def test_muscle_mention_ignores_vai_tro(self) -> None:
        self.assertEqual(mentioned_muscles("cách tập cho vai to"), ["vai"])
        self.assertEqual(mentioned_muscles("vai trò của squat"), [])


if __name__ == "__main__":
    unittest.main()
