"""Checks the offline evaluation calculations and resumable result file."""

import json
from pathlib import Path
import tempfile
import unittest

from app.scripts.evaluate_chatbot import compact_results, read_results, rouge_l_f1, token_f1


class EvaluationMetricsTest(unittest.TestCase):
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
