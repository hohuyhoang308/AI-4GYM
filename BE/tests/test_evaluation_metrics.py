"""Checks the offline evaluation calculations and resumable result file."""

import json
from pathlib import Path
import tempfile
import unittest

from app.scripts.evaluate_chatbot import compact_results, grade, read_results, required_condition_cap, rouge_l_f1, token_f1


class EvaluationMetricsTest(unittest.TestCase):
    def test_cardio_target_is_mandatory_for_full_credit(self) -> None:
        reference = "Tối thiểu 150 phút cardio cường độ vừa phải mỗi tuần và 2-3 buổi tập sức mạnh."
        cases = [
            ("Cardio 3–5 buổi/tuần, mỗi buổi 20–30 phút.", 1),
            ("Cardio 5 buổi/tuần, mỗi buổi 30 phút.", 2),
            ("Cardio ít nhất 150 phút mỗi tuần.", 2),
            ("Cardio 3 buổi/tuần, mỗi buổi 50 phút.", 2),
            ("Cardio 4 buổi/tuần, mỗi buổi 30 phút.", 1),
        ]
        for answer, expected in cases:
            with self.subTest(answer=answer):
                self.assertEqual(required_condition_cap(reference, answer)[0], expected)
        self.assertEqual(required_condition_cap(
            "Lịch này tương đương 150 phút hoạt động aerobic mỗi tuần.",
            "Đi bộ 5–10 phút mỗi ngày rồi tăng dần sau 2 tuần."
        )[0], 1)

    def test_judge_cannot_override_mandatory_numeric_condition(self) -> None:
        class OvergenerousJudge:
            def invoke(self, messages):
                return type("Reply", (), {"content": '{"score": 2, "reason": "Đủ ý"}'})()

        score, reason = grade(OvergenerousJudge(), "Cân bằng cardio và tạ?",
                              "Tối thiểu 150 phút cardio mỗi tuần và tập tạ 2 buổi.",
                              "Cardio 3–5 buổi/tuần, mỗi buổi 20–30 phút; tập tạ 2 buổi.")
        self.assertEqual(score, 1)
        self.assertIn("150 phút", reason)

    def test_overlap_metrics_reward_matching_words_and_order(self) -> None:
        self.assertEqual(token_f1("plank tăng sức mạnh", "plank tăng sức mạnh"), 1.0)
        self.assertEqual(rouge_l_f1("plank tăng sức mạnh", "plank tăng sức mạnh"), 1.0)
        self.assertEqual(token_f1("plank tăng sức mạnh", "sức mạnh tăng plank"), 1.0)
        self.assertLess(rouge_l_f1("plank tăng sức mạnh", "sức mạnh tăng plank"), 1.0)
        self.assertEqual(token_f1("plank", "squat"), 0.0)

    def test_resume_uses_latest_grade_and_compacts_in_test_order(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evaluation_results.jsonl"
            path.write_text('\n'.join(json.dumps(row) for row in [
                {"id": "qa-2", "judge_score": 2},
                {"id": "qa-1", "judge_score": 0},
                {"id": "qa-2", "judge_score": 1},
            ]) + '\n', encoding="utf-8")
            latest = read_results(path)
            self.assertEqual(latest["qa-2"]["judge_score"], 1)
            compact_results(path, [{"id": "qa-1"}, {"id": "qa-2"}], latest)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["id"] for row in rows], ["qa-1", "qa-2"])
            self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
