"""Check the committed dataset and Excel report without MySQL or Ollama."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from openpyxl import load_workbook

from app.core.config import ROOT, settings
from app.services.knowledge import normalize, read_qa_excel


REPORT = ROOT.parent / "reports" / "AI-4GYM_train_test_report.xlsx"
RESULTS = ROOT.parent / "reports" / "evaluation_results.jsonl"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(report_path: Path = REPORT, results_path: Path = RESULTS) -> dict:
    raw = read_qa_excel()
    all_rows = json.loads(settings.qa_json_path.read_text(encoding="utf-8"))
    train = json.loads(settings.train_json_path.read_text(encoding="utf-8"))
    test = json.loads(settings.test_json_path.read_text(encoding="utf-8"))
    manifest = json.loads(settings.split_manifest_path.read_text(encoding="utf-8"))

    require(raw == all_rows, "qa.json khác dữ liệu Excel gốc")
    require(manifest["source_sha256"] == sha256(settings.excel_path.read_bytes()).hexdigest(), "Hash Excel gốc khác manifest")
    require((len(all_rows), len(train), len(test)) == (
        manifest["total_rows"], manifest["train_rows"], manifest["test_rows"]
    ), "Số dòng train/test khác manifest")
    ids = [row["id"] for row in all_rows]
    train_ids = {row["id"] for row in train}
    test_ids = {row["id"] for row in test}
    require(len(ids) == len(set(ids)) and train_ids.isdisjoint(test_ids) and train_ids | test_ids == set(ids),
            "ID train/test thiếu, trùng hoặc lẫn nhau")
    require({normalize(row["question"]).strip() for row in train}.isdisjoint(
        {normalize(row["question"]).strip() for row in test}), "Câu hỏi trùng giữa train và test")
    train_tokens = [set(normalize(row["question"]).split()) for row in train]
    near_duplicate_pairs = 0
    for row in test:
        tokens = set(normalize(row["question"]).split())
        if any(len(tokens & other) / len(tokens | other) >= 0.8
               for other in train_tokens if tokens | other):
            near_duplicate_pairs += 1

    results = {}
    test_hash = sha256(settings.test_json_path.read_bytes()).hexdigest()
    if results_path.exists():
        for line_number, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            item = json.loads(line)
            require(item.get("id") in test_ids and item.get("test_sha256") == test_hash,
                    f"Kết quả dòng {line_number} không thuộc tập test hiện tại")
            require(item.get("source_sha256") == manifest["source_sha256"] and
                    item.get("chat_model") == settings.chat_model and item.get("embed_model") == settings.embed_model,
                    f"Kết quả dòng {line_number} khác dữ liệu/model hiện tại")
            if item.get("judge_score") is not None:
                require(type(item["judge_score"]) is int and item["judge_score"] in (0, 1, 2),
                        f"Điểm không hợp lệ ở dòng {line_number}")
                results[item["id"]] = item

    workbook = load_workbook(report_path, read_only=True, data_only=False)
    try:
        require(workbook.sheetnames == ["Tong quan", "Train 80", "Test 20", "Danh gia Test"], "Thiếu hoặc thừa sheet báo cáo")
        overview = workbook["Tong quan"]
        require([overview[f"B{row}"].value for row in (7, 8, 9)] ==
                [len(train), len(test), len(all_rows)], "Tổng quan sai số dòng")
        report_count_text = overview["B16"].value
        require(isinstance(report_count_text, str) and report_count_text.endswith(f"/{len(test)}"),
                "Tổng quan sai định dạng số câu đã chấm")
        report_count = int(report_count_text.split("/")[0])
        require(report_count <= len(results), "Excel báo cáo có nhiều kết quả hơn JSONL")
        scores = Counter(item["judge_score"] for item in results.values())
        for sheet_name, rows in (("Train 80", train), ("Test 20", test)):
            sheet = workbook[sheet_name]
            require(sheet.max_row == len(rows) + 1, f"Sheet {sheet_name} sai số dòng")
            for number, (cells, row) in enumerate(zip(sheet.iter_rows(min_row=2, values_only=True), rows), 2):
                require(cells[0] == row["id"] and cells[2] == row["question"] and
                        cells[3] == row["answer"],
                        f"Sheet {sheet_name} sai tại dòng {number}")
        sheet = workbook["Danh gia Test"]
        require(sheet.max_row == len(test) + 1, "Sheet đánh giá sai số dòng")
        manually_reviewed = 0
        reported_scores = Counter()
        for number, (cells, row) in enumerate(zip(sheet.iter_rows(min_row=2, values_only=True), test), 2):
            result = results.get(row["id"])
            require(cells[0] == row["id"] and cells[1] == row["question"] and
                    cells[2] == row["answer"],
                    f"Sheet đánh giá sai câu hỏi/đáp án tại dòng {number}")
            if cells[4] is not None:
                require(result is not None and cells[3] == result["answer"] and
                        cells[4] == result["judge_score"],
                        f"Sheet đánh giá sai kết quả tại dòng {number}")
                reported_scores[cells[4]] += 1
            else:
                require(cells[3] is None, f"Sheet đánh giá có câu trả lời chưa chấm tại dòng {number}")
            manually_reviewed += cells[12] in (0, 1)
        require(sum(reported_scores.values()) == report_count and
                [overview[f"B{row}"].value for row in (17, 18, 19)] ==
                [reported_scores[2], reported_scores[1], reported_scores[0]],
                "Tổng quan không khớp kết quả trong sheet đánh giá")
    finally:
        workbook.close()
    return {
        "total": len(all_rows), "train": len(train), "test": len(test),
        "evaluated": len(results), "remaining": len(test) - len(results),
        "reported_in_excel": report_count, "report_synced": report_count == len(results),
        "scores": dict(sorted(scores.items())), "manually_reviewed": manually_reviewed,
        "near_duplicate_test_questions_jaccard_0_8": near_duplicate_pairs,
        "artifact_integrity": "PASS", "evaluation_complete": len(results) == len(test),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
