import re
from functools import lru_cache

from app.services.knowledge import load_qa_json, normalize


FITNESS_TERMS = {
    "gym", "fitness", "the hinh", "the chat", "the luc", "hoat dong the chat", "bai tap", "tap luyen", "buoi tap", "phong tap", "lich tap", "co bap", "nhom co", "co nguc", "co lung", "co tay", "co chan", "co bung", "co vai", "co mong",
    "tang co", "giam mo", "giam can", "squat", "deadlift", "bench press", "plank", "push up", "hit dat", "lunge", "burpee", "superset", "hiit", "aerobic", "cardio", "workout", "split", "push pull legs", "upper lower",
    "nang ta", "ta don", "ta tay", "tap ta", "phong gym", "khoi dong", "phuc hoi", "gian co", "do linh hoat", "tu the", "hiep tap", "khang luc", "qua tai tien trien", "protein", "calo", "dinh duong", "van dong", "the duc", "yoga", "pilates", "chay bo", "di bo", "boi loi", "dap xe", "kickboxing", "tim mach", "can nang", "suc ben", "suc manh", "chan thuong",
}

MUSCLE_NAMES = ("nguc", "lung", "chan", "tay", "vai", "bung", "mong")
MUSCLE_PATTERN = "(?:" + "|".join(MUSCLE_NAMES) + ")"
TRAINING_MUSCLE_PATTERN = re.compile(
    rf"\b(?:tap|ren|luyen)\s+(?:(?:cho|co|nhom|bap|phan)\s+){{0,3}}{MUSCLE_PATTERN}\b"
)


def mentioned_muscles(question: str) -> list[str]:
    normalized = normalize(question)
    return [
        muscle for muscle in MUSCLE_NAMES
        if re.search(r"(?<!\w)" + muscle + r"(?!\w)", normalized)
        and not (muscle == "vai" and re.search(r"\bvai tro\b", normalized))
    ]


@lru_cache(maxsize=1)
def known_questions() -> set[str]:
    return {normalize(row["question"]).strip() for row in load_qa_json()}


def in_scope(question: str, has_context: bool = False) -> bool:
    normalized = normalize(question)
    if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", normalized) for term in FITNESS_TERMS):
        return True
    if TRAINING_MUSCLE_PATTERN.search(normalized) or re.search(r"\breps?\b", normalized):
        return True
    if mentioned_muscles(question) and re.search(r"\b(?:tap|set|sets|hiep|lan lap)\b", normalized):
        return True
    if normalized.strip() in known_questions():
        return True
    return has_context and bool(re.search(r"\b(con|neu|vay|the|doi|sao|bao nhieu|ngay|tuan|nua)\b", normalized))


def requested_days(question: str) -> int | None:
    normalized = normalize(question)
    match = re.search(r"(?<!\d)([1-6])\s*(?:buoi|ngay)(?:\s*/\s*tuan|\s*(?:moi|mot)?\s*tuan)?", normalized)
    return int(match.group(1)) if match else None
