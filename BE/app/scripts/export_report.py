"""Export the RAG train/test split and a manual evaluation sheet to Excel."""

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from app.core.config import ROOT, settings
from app.services.index import vector_store
from app.services.knowledge import load_exercises, normalize


DEFAULT_OUTPUT = ROOT.parent / "reports" / "AI-4GYM_train_test_report.xlsx"
DEFAULT_RESULTS = ROOT.parent / "reports" / "evaluation_results.jsonl"
DARK = "173B2A"
GREEN = "6B9F45"
PALE = "EAF3E7"
WHITE = "FFFFFF"
GRAY = "64776A"


def load_verified_data() -> tuple[list[dict], list[dict], list[dict], dict, int, int]:
    for path in (settings.excel_path, settings.qa_json_path, settings.train_json_path, settings.test_json_path, settings.split_manifest_path):
        if not path.is_file():
            raise FileNotFoundError(f"Thiếu {path}. Chạy python -m app.scripts.ingest trước.")

    all_rows = json.loads(settings.qa_json_path.read_text(encoding="utf-8"))
    train_rows = json.loads(settings.train_json_path.read_text(encoding="utf-8"))
    test_rows = json.loads(settings.test_json_path.read_text(encoding="utf-8"))
    manifest = json.loads(settings.split_manifest_path.read_text(encoding="utf-8"))
    all_ids = {row["id"] for row in all_rows}
    train_ids = {row["id"] for row in train_rows}
    test_ids = {row["id"] for row in test_rows}
    train_questions = {normalize(row["question"]).strip() for row in train_rows}
    test_questions = {normalize(row["question"]).strip() for row in test_rows}
    source_hash = sha256(settings.excel_path.read_bytes()).hexdigest()

    if train_ids | test_ids != all_ids or train_ids & test_ids or train_questions & test_questions:
        raise ValueError("Tập train/test bị thiếu, trùng ID hoặc có câu hỏi trùng giữa hai tập")
    if (
        len(all_rows) != manifest["total_rows"]
        or len(train_rows) != manifest["train_rows"]
        or len(test_rows) != manifest["test_rows"]
        or source_hash != manifest["source_sha256"]
    ):
        raise ValueError("Dữ liệu hoặc file Excel đã đổi. Chạy lại python -m app.scripts.ingest")

    exercises = load_exercises()
    expected_index_ids = train_ids | {f"exercise-{exercise['id']}" for exercise in exercises}
    indexed_ids = set(vector_store().get(include=[])["ids"])
    if indexed_ids != expected_index_ids:
        raise ValueError("Chỉ mục Chroma không khớp tập train. Chạy lại python -m app.scripts.ingest")

    duplicate_groups = sum(count > 1 for count in Counter(normalize(row["question"]).strip() for row in all_rows).values())
    return all_rows, train_rows, test_rows, manifest, len(exercises), duplicate_groups


def load_evaluation_results(test_rows: list[dict], results_path: Path = DEFAULT_RESULTS) -> dict[str, dict]:
    if not results_path.exists():
        return {}
    expected_hash = sha256(settings.test_json_path.read_bytes()).hexdigest()
    expected_source_hash = sha256(settings.excel_path.read_bytes()).hexdigest()
    test_ids = {row["id"] for row in test_rows}
    results = {}
    for line_number, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        result = json.loads(line)
        if result.get("id") not in test_ids or result.get("test_sha256") != expected_hash or result.get("chat_model") != settings.chat_model or result.get("embed_model") != settings.embed_model or result.get("source_sha256") != expected_source_hash:
            raise ValueError(f"Kết quả đánh giá không khớp tập test/model ở dòng {line_number}")
        if result.get("judge_score") not in (0, 1, 2):
            raise ValueError(f"Điểm chấm không hợp lệ ở dòng {line_number}")
        results[result["id"]] = result
    return results


def style_header(cell) -> None:
    cell.fill = PatternFill("solid", fgColor=DARK)
    cell.font = Font(name="Aptos", size=11, bold=True, color=WHITE)
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    cell.border = Border(bottom=Side(style="thin", color=GREEN))


def add_data_sheet(workbook: Workbook, title: str, rows: list[dict]) -> None:
    sheet = workbook.create_sheet(title)
    sheet.append(["ID", "STT", "Câu hỏi", "Câu trả lời tham chiếu", "Nguồn", "Dòng Excel"])
    for cell in sheet[1]:
        style_header(cell)
    sheet.row_dimensions[1].height = 28
    for row in rows:
        sheet.append([row["id"], row.get("stt"), row["question"], row["answer"], row["source"], row["excel_row"]])
    widths = {"A": 15, "B": 9, "C": 62, "D": 96, "E": 22, "F": 13}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=cell.column in (3, 4))
        if row[0].row % 2 == 0:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor="F4F8F2")
        sheet.row_dimensions[row[0].row].height = 44
    sheet.freeze_panes = "C2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.print_title_rows = "1:1"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.orientation = "landscape"


def load_manual_reviews(output: Path, test_rows: list[dict]) -> dict[str, tuple[int | None, str | None]]:
    if not output.exists():
        return {}
    previous = load_workbook(output, read_only=True)
    try:
        if "Danh gia Test" not in previous:
            return {}
        sheet = previous["Danh gia Test"]
        if sheet["M1"].value != "Duyệt tay (1/0)":
            return {}
        test_ids = {row["id"] for row in test_rows}
        reviews = {}
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0] not in test_ids:
                continue
            manual_score = row[12]
            manual_note = row[13]
            if (type(manual_score) is int and manual_score in (0, 1)) or manual_note:
                reviews[row[0]] = (manual_score if type(manual_score) is int and manual_score in (0, 1) else None, manual_note)
        return reviews
    finally:
        previous.close()


def add_evaluation_sheet(workbook: Workbook, rows: list[dict], results: dict[str, dict], manual_reviews: dict[str, tuple[int | None, str | None]]) -> None:
    sheet = workbook.create_sheet("Danh gia Test")
    sheet.append(["ID", "Câu hỏi", "Đáp án tham chiếu", "Câu trả lời chatbot", "Điểm AI (0-2)", "Lý do chấm AI", "Token F1", "ROUGE-L F1", "Số nguồn", "ID nguồn RAG", "Thời gian (giây)", "Dòng Excel", "Duyệt tay (1/0)", "Ghi chú duyệt tay"])
    for cell in sheet[1]:
        style_header(cell)
    sheet.row_dimensions[1].height = 30
    for row in rows:
        result = results.get(row["id"], {})
        sources = result.get("sources", [])
        manual_score, manual_note = manual_reviews.get(row["id"], (None, None))
        sheet.append([
            row["id"], row["question"], row["answer"], result.get("answer"), result.get("judge_score"),
            result.get("judge_reason"), result.get("token_f1"), result.get("rouge_l_f1"), len(sources) if result else None,
            ", ".join(source["id"] for source in sources) if result else None, result.get("seconds"), row["excel_row"], manual_score, manual_note,
        ])
    widths = {"A": 15, "B": 60, "C": 88, "D": 88, "E": 16, "F": 58, "G": 15, "H": 17, "I": 13, "J": 48, "K": 18, "L": 13, "M": 19, "N": 44}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=cell.column in (2, 3, 4, 6, 10, 14))
        sheet.row_dimensions[row[0].row].height = 52
    for row in sheet.iter_rows(min_row=2):
        for column in (7, 8):
            row[column - 1].number_format = "0.0%"
    validation = DataValidation(type="whole", operator="between", formula1="0", formula2="1", allow_blank=True)
    validation.error = "Chỉ nhập 1 (đạt) hoặc 0 (không đạt)."
    validation.errorTitle = "Giá trị không hợp lệ"
    validation.showErrorMessage = True
    sheet.add_data_validation(validation)
    validation.add(f"M2:M{len(rows) + 1}")
    sheet.conditional_formatting.add(f"E2:E{len(rows) + 1}", FormulaRule(formula=["AND(ISNUMBER($E2),$E2=2)"], fill=PatternFill("solid", fgColor="DDF2D4")))
    sheet.conditional_formatting.add(f"E2:E{len(rows) + 1}", FormulaRule(formula=["AND(ISNUMBER($E2),$E2=0)"], fill=PatternFill("solid", fgColor="FBE0DA")))
    sheet.freeze_panes = "D2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.print_title_rows = "1:1"


def add_overview(workbook: Workbook, manifest: dict, exercise_count: int, duplicate_groups: int, results: dict[str, dict]) -> None:
    sheet = workbook.active
    sheet.title = "Tong quan"
    sheet.sheet_view.showGridLines = False
    for column, width in {"A": 26, "B": 18, "C": 17, "D": 32, "E": 4, "F": 18, "G": 18, "H": 18}.items():
        sheet.column_dimensions[column].width = width
    sheet.merge_cells("A1:H2")
    title = sheet["A1"]
    title.value = "AI-4GYM  |  BÁO CÁO CHIA DỮ LIỆU TRAIN / TEST"
    title.fill = PatternFill("solid", fgColor=DARK)
    title.font = Font(name="Aptos Display", size=20, bold=True, color=WHITE)
    title.alignment = Alignment(vertical="center", horizontal="center")
    sheet.row_dimensions[1].height = 27
    sheet.row_dimensions[2].height = 27
    sheet.merge_cells("A3:H3")
    sheet["A3"] = f"Nguồn: {manifest['source']}  •  Tạo lúc: {datetime.now():%d/%m/%Y %H:%M}  •  Seed: {manifest['seed']}"
    sheet["A3"].font = Font(name="Aptos", size=10, color=GRAY)
    sheet["A3"].alignment = Alignment(horizontal="center")

    for column, value in zip("ABCD", ["Tập dữ liệu", "Số câu", "Tỷ lệ", "Vai trò"]):
        cell = sheet[f"{column}6"]
        cell.value = value
        style_header(cell)
    summary_rows = [
        (7, "Train / corpus", manifest["train_rows"], manifest["train_percent"] / 100, "Lập chỉ mục RAG"),
        (8, "Test giữ riêng", manifest["test_rows"], manifest["test_percent"] / 100, "Không đưa vào Chroma"),
        (9, "Tổng", manifest["total_rows"], 1, "Toàn bộ Excel gốc"),
    ]
    for number, label, count, percent, purpose in summary_rows:
        sheet[f"A{number}"] = label
        sheet[f"B{number}"] = count
        sheet[f"C{number}"] = percent
        sheet[f"C{number}"].number_format = "0.0%"
        sheet[f"D{number}"] = purpose
        for cell in sheet[number][:4]:
            cell.fill = PatternFill("solid", fgColor=PALE if number % 2 else "F7FAF5")
            cell.font = Font(name="Aptos", size=11, bold=number == 9, color=DARK)
            cell.alignment = Alignment(vertical="center")
        sheet.row_dimensions[number].height = 30

    chart = BarChart()
    chart.title = "Số câu theo tập dữ liệu"
    chart.y_axis.title = "Số câu"
    chart.x_axis.title = "Tập"
    chart.add_data(Reference(sheet, min_col=2, min_row=6, max_row=8), titles_from_data=True)
    chart.set_categories(Reference(sheet, min_col=1, min_row=7, max_row=8))
    chart.height = 7
    chart.width = 14
    chart.legend = None
    sheet.add_chart(chart, "F6")

    details = [
        (11, "Bài tập bổ sung", exercise_count),
        (12, "Tài liệu trong Chroma", manifest["train_rows"] + exercise_count),
        (13, "Nhóm câu hỏi trùng", duplicate_groups),
        (14, "Fine-tune Qwen", "Không"),
    ]
    for number, label, value in details:
        sheet[f"A{number}"] = label
        sheet[f"B{number}"] = value
        sheet[f"A{number}"].font = Font(name="Aptos", size=11, bold=True, color=DARK)
        sheet[f"B{number}"].font = Font(name="Aptos", size=11, color=DARK)
        sheet.row_dimensions[number].height = 25

    completed = len(results)
    passed = sum(result["judge_score"] == 2 for result in results.values())
    partial = sum(result["judge_score"] == 1 for result in results.values())
    failed = sum(result["judge_score"] == 0 for result in results.values())
    summary = [
        (16, "Đã chạy test", f"{completed}/{manifest['test_rows']}"),
        (17, "Đạt tự động (2/2)", passed),
        (18, "Đúng một phần (1/2)", partial),
        (19, "Sai/từ chối (0/2)", failed),
        (20, "Tỷ lệ đạt tự động", passed / completed if completed else "Chưa chạy"),
        (21, "Token F1 trung bình", sum(result["token_f1"] for result in results.values()) / completed if completed else "Chưa chạy"),
        (22, "ROUGE-L F1 trung bình", sum(result["rouge_l_f1"] for result in results.values()) / completed if completed else "Chưa chạy"),
        (23, "Thời gian TB (giây)", sum(result["seconds"] for result in results.values()) / completed if completed else "Chưa chạy"),
    ]
    for number, label, value in summary:
        sheet[f"A{number}"] = label
        sheet[f"B{number}"] = value
        sheet[f"A{number}"].font = Font(name="Aptos", size=11, bold=True, color=DARK)
        sheet[f"B{number}"].font = Font(name="Aptos", size=11, bold=number == 20, color=GREEN if number == 20 else DARK)
        sheet.row_dimensions[number].height = 24
    for number in (20, 21, 22):
        sheet[f"B{number}"].number_format = "0.0%"
    sheet["B23"].number_format = "0.0"
    sheet["A25"] = "Tỷ lệ duyệt tay"
    sheet["A25"].font = Font(name="Aptos", size=11, bold=True, color=DARK)
    test_end = manifest["test_rows"] + 1
    sheet["B25"] = f'=IF(COUNT(\'Danh gia Test\'!M2:M{test_end})=0,"Chưa chấm",SUM(\'Danh gia Test\'!M2:M{test_end})/COUNT(\'Danh gia Test\'!M2:M{test_end}))'
    sheet["B25"].number_format = "0.0%"
    sheet["B25"].font = Font(name="Aptos", size=11, color=GREEN)
    sheet.merge_cells("A27:H28")
    sheet["A27"] = "Điểm 0/1/2 do Qwen local chấm theo đáp án tham chiếu, không phải đánh giá độc lập của con người. Tỷ lệ đạt = số câu điểm 2 / số câu đã chạy; khi đủ 193 câu mới là kết quả toàn bộ test. Token F1 và ROUGE-L chỉ đo mức trùng từ, không chứng minh câu trả lời đúng. Có thể duyệt tay ở sheet 'Danh gia Test'."
    sheet["A27"].alignment = Alignment(wrap_text=True, vertical="center")
    sheet["A27"].fill = PatternFill("solid", fgColor=PALE)
    sheet["A27"].font = Font(name="Aptos", size=10, color=DARK)
    sheet.row_dimensions[27].height = 34
    sheet.row_dimensions[28].height = 34

    checks = [
        (31, "Tổng train + test", f"{manifest['train_rows']} + {manifest['test_rows']} = {manifest['total_rows']}", "ĐẠT"),
        (32, "Câu hỏi trùng giữa 2 tập", 0, "ĐẠT"),
        (33, "ID test trong Chroma", 0, "ĐẠT"),
        (34, "Số tài liệu Chroma", manifest["train_rows"] + exercise_count, "ĐẠT"),
    ]
    for number, label, value, result in checks:
        sheet[f"A{number}"] = label
        sheet[f"B{number}"] = value
        sheet[f"C{number}"] = result
        sheet[f"C{number}"].font = Font(name="Aptos", size=10, bold=True, color=GREEN)
        sheet.row_dimensions[number].height = 23
    sheet["A30"] = "KIỂM TRA TÍNH TOÀN VẸN"
    sheet["A30"].font = Font(name="Aptos", size=11, bold=True, color=DARK)
    sheet["A36"] = "SHA-256 Excel gốc"
    sheet["A36"].font = Font(name="Aptos", size=10, bold=True, color=GRAY)
    sheet.merge_cells("B36:H36")
    sheet["B36"] = manifest["source_sha256"]
    sheet["B36"].font = Font(name="Consolas", size=9, color=GRAY)
    sheet["A38"] = "Model trả lời/chấm"
    sheet["B38"] = settings.chat_model
    sheet["A39"] = "Model embedding"
    sheet["B39"] = settings.embed_model
    sheet["A40"] = "Quy tắc chấm tự động"
    sheet["B40"] = "Qwen judge v2: 0/1/2 theo đáp án tham chiếu"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.orientation = "landscape"


def export_report(output: Path = DEFAULT_OUTPUT, results_path: Path = DEFAULT_RESULTS) -> Path:
    _, train_rows, test_rows, manifest, exercise_count, duplicate_groups = load_verified_data()
    results = load_evaluation_results(test_rows, results_path)
    manual_reviews = load_manual_reviews(output, test_rows)
    workbook = Workbook()
    add_overview(workbook, manifest, exercise_count, duplicate_groups, results)
    add_data_sheet(workbook, "Train 80", train_rows)
    add_data_sheet(workbook, "Test 20", test_rows)
    add_evaluation_sheet(workbook, test_rows, results, manual_reviews)
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Xuất báo cáo train/test AI-4GYM ra Excel")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Đường dẫn file .xlsx đầu ra")
    args = parser.parse_args()
    print(f"Report saved: {export_report(args.output).resolve()}")


if __name__ == "__main__":
    main()
