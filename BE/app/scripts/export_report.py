"""Export the RAG train/test split and a manual evaluation sheet to Excel."""

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from app.core.config import ROOT, settings
from app.services.index import vector_store
from app.services.knowledge import load_exercises, normalize


DEFAULT_OUTPUT = ROOT.parent / "reports" / "AI-4GYM_train_test_report.xlsx"
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


def add_evaluation_sheet(workbook: Workbook, rows: list[dict]) -> None:
    sheet = workbook.create_sheet("Danh gia Test")
    sheet.append(["ID", "Câu hỏi", "Đáp án tham chiếu", "Câu trả lời chatbot", "Đạt? (1/0)", "Ghi chú", "Dòng Excel"])
    for cell in sheet[1]:
        style_header(cell)
    sheet.row_dimensions[1].height = 30
    for row in rows:
        sheet.append([row["id"], row["question"], row["answer"], None, None, None, row["excel_row"]])
    widths = {"A": 15, "B": 60, "C": 88, "D": 88, "E": 15, "F": 42, "G": 13}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=cell.column in (2, 3, 4, 6))
        sheet.row_dimensions[row[0].row].height = 52
    validation = DataValidation(type="whole", operator="between", formula1="0", formula2="1", allow_blank=True)
    validation.error = "Chỉ nhập 1 (đạt) hoặc 0 (không đạt)."
    validation.errorTitle = "Giá trị không hợp lệ"
    validation.showErrorMessage = True
    sheet.add_data_validation(validation)
    validation.add(f"E2:E{len(rows) + 1}")
    sheet.conditional_formatting.add(f"E2:E{len(rows) + 1}", FormulaRule(formula=["AND(ISNUMBER($E2),$E2=1)"], fill=PatternFill("solid", fgColor="DDF2D4")))
    sheet.conditional_formatting.add(f"E2:E{len(rows) + 1}", FormulaRule(formula=["AND(ISNUMBER($E2),$E2=0)"], fill=PatternFill("solid", fgColor="FBE0DA")))
    sheet.freeze_panes = "D2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.print_title_rows = "1:1"


def add_overview(workbook: Workbook, manifest: dict, exercise_count: int, duplicate_groups: int) -> None:
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

    test_end = manifest["test_rows"] + 1
    sheet["A16"] = "Độ chính xác sau chấm"
    sheet["A16"].font = Font(name="Aptos", size=11, bold=True, color=DARK)
    sheet["B16"] = f'=IF(COUNT(\'Danh gia Test\'!E2:E{test_end})=0,"Chưa chấm",SUM(\'Danh gia Test\'!E2:E{test_end})/COUNT(\'Danh gia Test\'!E2:E{test_end}))'
    sheet["B16"].number_format = "0.0%"
    sheet["B16"].font = Font(name="Aptos", size=12, bold=True, color=GREEN)
    sheet.merge_cells("A18:H19")
    sheet["A18"] = "Cách chấm: mở sheet 'Danh gia Test', điền câu trả lời AI và đánh dấu 1 nếu đạt, 0 nếu không đạt. Ô độ chính xác sẽ tự tính khi mở bằng Excel. Tỷ lệ 80/20 là tỷ lệ chia dữ liệu, chưa phải độ chính xác của chatbot."
    sheet["A18"].alignment = Alignment(wrap_text=True, vertical="center")
    sheet["A18"].fill = PatternFill("solid", fgColor=PALE)
    sheet["A18"].font = Font(name="Aptos", size=10, color=DARK)
    sheet.row_dimensions[18].height = 30
    sheet.row_dimensions[19].height = 30

    checks = [
        (22, "Tổng train + test", f"{manifest['train_rows']} + {manifest['test_rows']} = {manifest['total_rows']}", "ĐẠT"),
        (23, "Câu hỏi trùng giữa 2 tập", 0, "ĐẠT"),
        (24, "ID test trong Chroma", 0, "ĐẠT"),
        (25, "Số tài liệu Chroma", manifest["train_rows"] + exercise_count, "ĐẠT"),
    ]
    for number, label, value, result in checks:
        sheet[f"A{number}"] = label
        sheet[f"B{number}"] = value
        sheet[f"C{number}"] = result
        sheet[f"C{number}"].font = Font(name="Aptos", size=10, bold=True, color=GREEN)
        sheet.row_dimensions[number].height = 23
    sheet["A21"] = "KIỂM TRA TÍNH TOÀN VẸN"
    sheet["A21"].font = Font(name="Aptos", size=11, bold=True, color=DARK)
    sheet["A27"] = "SHA-256 Excel gốc"
    sheet["A27"].font = Font(name="Aptos", size=10, bold=True, color=GRAY)
    sheet.merge_cells("B27:H27")
    sheet["B27"] = manifest["source_sha256"]
    sheet["B27"].font = Font(name="Consolas", size=9, color=GRAY)
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.orientation = "landscape"


def export_report(output: Path = DEFAULT_OUTPUT) -> Path:
    _, train_rows, test_rows, manifest, exercise_count, duplicate_groups = load_verified_data()
    workbook = Workbook()
    add_overview(workbook, manifest, exercise_count, duplicate_groups)
    add_data_sheet(workbook, "Train 80", train_rows)
    add_data_sheet(workbook, "Test 20", test_rows)
    add_evaluation_sheet(workbook, test_rows)
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
