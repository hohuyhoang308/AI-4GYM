"""Checks that held-out questions never enter the RAG index."""

import json
import unittest

from app.core.config import settings
from app.services.dataset import TEST_RATIO, split_qa_rows
from app.services.index import indexed_count, vector_store
from app.services.knowledge import load_exercises, load_qa_json, normalize


class DatasetSplitTest(unittest.TestCase):
    def test_split_is_reproducible_and_has_no_question_leakage(self) -> None:
        rows = load_qa_json()
        train, test = split_qa_rows(rows)
        reverse_train, reverse_test = split_qa_rows(list(reversed(rows)))

        self.assertEqual(len(test), round(len(rows) * TEST_RATIO))
        self.assertEqual({row["id"] for row in train + test}, {row["id"] for row in rows})
        self.assertFalse({normalize(row["question"]) for row in train} & {normalize(row["question"]) for row in test})
        self.assertEqual({row["id"] for row in train}, {row["id"] for row in reverse_train})
        self.assertEqual({row["id"] for row in test}, {row["id"] for row in reverse_test})

    def test_exported_test_cases_are_absent_from_index(self) -> None:
        if not settings.test_json_path.exists():
            self.skipTest("Chạy python -m app.scripts.ingest trước")
        test_rows = json.loads(settings.test_json_path.read_text(encoding="utf-8"))
        train_rows = json.loads(settings.train_json_path.read_text(encoding="utf-8"))
        count = indexed_count()
        if count == 0:
            self.skipTest("Chưa có chỉ mục Chroma")

        indexed_ids = set(vector_store().get(include=[])["ids"])
        self.assertEqual(count, len(train_rows) + len(load_exercises()))
        self.assertFalse(indexed_ids & {row["id"] for row in test_rows})
        self.assertTrue({row["id"] for row in train_rows} <= indexed_ids)


if __name__ == "__main__":
    unittest.main()
