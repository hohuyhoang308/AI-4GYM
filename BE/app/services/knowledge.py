import json
import unicodedata
from pathlib import Path

from langchain_core.documents import Document
from openpyxl import load_workbook

from app.core.config import settings


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in text if unicodedata.category(char) != "Mn").replace("đ", "d")


def load_exercises() -> list[dict]:
    return json.loads(settings.exercise_path.read_text(encoding="utf-8"))


def matching_exercises(muscle: str | None = None) -> list[dict]:
    exercises = load_exercises()
    if not muscle:
        return exercises
    term = normalize(muscle).strip()
    matches = [
        exercise for exercise in exercises
        if any(term in normalize(name) for name in exercise["primary_muscles"] + exercise["secondary_muscles"])
    ]
    return sorted(matches, key=lambda exercise: not any(term in normalize(name) for name in exercise["primary_muscles"]))


def read_qa_excel(path: Path | None = None) -> list[dict]:
    workbook = load_workbook(path or settings.excel_path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        headers = [str(value or "").strip().casefold() for value in next(sheet.values)]
        required = {"question", "answer"}
        if not required.issubset(headers):
            raise ValueError(f"Excel cần các cột: {', '.join(sorted(required))}")
        indices = {name: headers.index(name) for name in required}
        source_index = headers.index("source") if "source" in headers else None
        stt_index = headers.index("stt") if "stt" in headers else None
        rows = []
        for excel_row, values in enumerate(sheet.values, start=1):
            if excel_row == 1:
                continue
            question = str(values[indices["question"]] or "").strip()
            answer = str(values[indices["answer"]] or "").strip()
            source = str(values[source_index] or "").strip() if source_index is not None else settings.excel_path.name
            if not question or not answer:
                continue
            stt = values[stt_index] if stt_index is not None else None
            rows.append({"id": f"qa-{excel_row}", "stt": stt, "question": question, "answer": answer, "source": source, "sheet": sheet.title, "excel_row": excel_row})
        return rows
    finally:
        workbook.close()


def export_qa_json() -> list[dict]:
    rows = read_qa_excel()
    settings.qa_json_path.parent.mkdir(parents=True, exist_ok=True)
    settings.qa_json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def load_qa_json() -> list[dict]:
    if not settings.qa_json_path.exists():
        return export_qa_json()
    return json.loads(settings.qa_json_path.read_text(encoding="utf-8"))


def build_documents(qa_rows: list[dict] | None = None) -> list[Document]:
    rows = qa_rows if qa_rows is not None else load_qa_json()
    documents = [
        Document(
            id=row["id"],
            page_content=f"Câu hỏi: {row['question']}\nCâu trả lời: {row['answer']}",
            metadata={"kind": "qa", "source": row["source"], "excel_row": row["excel_row"], "title": row["question"][:100]},
        )
        for row in rows
    ]
    for exercise in load_exercises():
        documents.append(Document(
            id=f"exercise-{exercise['id']}",
            page_content=(
                f"Bài tập: {exercise['name']}. Tên khác: {', '.join(exercise['aliases'])}. "
                f"Nhóm cơ chính: {', '.join(exercise['primary_muscles'])}. "
                f"Nhóm cơ phụ: {', '.join(exercise['secondary_muscles']) or 'không rõ'}. "
                f"Dụng cụ: {exercise['equipment']}.\n"
                + "\n".join(f"Bước {i}: {step}" for i, step in enumerate(exercise["steps"], 1))
                + "\nLỗi cần tránh: " + "; ".join(exercise["common_mistakes"])
            ),
            metadata={"kind": "exercise", "source": exercise["source"], "title": exercise["name"], "exercise_id": exercise["id"]},
        ))
    return documents
