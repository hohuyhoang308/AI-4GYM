"""Reproducible 80/20 split for the RAG corpus and held-out evaluation set."""

from collections import defaultdict
from hashlib import sha256
import json

from app.core.config import settings
from app.services.knowledge import load_qa_json, normalize, write_json


SPLIT_SEED = 42
TEST_RATIO = 0.20


def split_qa_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    if not rows:
        raise ValueError("Không có dữ liệu hỏi đáp để chia train/test")

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[normalize(row["question"]).strip()].append(row)

    target_test = round(len(rows) * TEST_RATIO)
    ordered_keys = sorted(groups, key=lambda key: sha256(f"{SPLIT_SEED}:{key}".encode("utf-8")).digest())
    train_rows: list[dict] = []
    test_rows: list[dict] = []
    for key in ordered_keys:
        group = groups[key]
        if len(test_rows) + len(group) <= target_test:
            test_rows.extend(group)
        else:
            train_rows.extend(group)

    if len(test_rows) != target_test:
        raise ValueError("Không thể chia đúng tỷ lệ 80/20 khi giữ các câu hỏi trùng cùng một tập")
    train_rows.sort(key=lambda row: row["excel_row"])
    test_rows.sort(key=lambda row: row["excel_row"])
    return train_rows, test_rows


def export_qa_splits(rows: list[dict] | None = None) -> dict:
    all_rows = rows if rows is not None else load_qa_json()
    train_rows, test_rows = split_qa_rows(all_rows)
    for path, split_rows in ((settings.train_json_path, train_rows), (settings.test_json_path, test_rows)):
        write_json(path, split_rows)

    manifest = {
        "seed": SPLIT_SEED,
        "split_method": "SHA-256 theo câu hỏi đã chuẩn hóa; câu hỏi trùng nằm cùng một tập",
        "source": settings.excel_path.name,
        "source_sha256": sha256(settings.excel_path.read_bytes()).hexdigest(),
        "total_rows": len(all_rows),
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
        "train_percent": round(len(train_rows) / len(all_rows) * 100, 2),
        "test_percent": round(len(test_rows) / len(all_rows) * 100, 2),
    }
    write_json(settings.split_manifest_path, manifest)
    return manifest


def load_train_json() -> list[dict]:
    if not settings.train_json_path.exists():
        export_qa_splits()
    return json.loads(settings.train_json_path.read_text(encoding="utf-8"))
