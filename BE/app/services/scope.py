import re
from functools import lru_cache

from app.services.dataset import load_train_json
from app.services.knowledge import normalize


FITNESS_TERMS = {
    "gym", "fitness", "the hinh", "the chat", "the luc", "hoat dong the chat", "bai tap", "tap luyen", "buoi tap", "phong tap", "lich tap", "co bap", "nhom co", "co nguc", "co lung", "co tay", "co chan", "co bung", "co vai", "co mong",
    "tang co", "giam mo", "giam can", "squat", "deadlift", "bench press", "plank", "push up", "hit dat", "lunge", "burpee", "superset", "hiit", "aerobic", "cardio", "workout", "split", "push pull legs", "upper lower",
    "nang ta", "ta don", "ta tay", "tap ta", "phong gym", "chong day", "day nguc", "keo xo", "cuon tay", "khoi dong", "phuc hoi", "gian co", "do linh hoat", "tu the", "hiep tap", "khang luc", "qua tai tien trien", "protein", "calo", "dinh duong", "van dong", "the duc", "yoga", "pilates", "chay bo", "di bo", "boi loi", "dap xe", "kickboxing", "tim mach", "can nang", "suc ben", "suc manh", "chan thuong",
    "nhin an", "ramadan", "nhin an gian doan", "thoi diem tap", "tap khi doi", "an uong truoc tap", "dung cu", "thiet bi tap", "khong dung cu", "bodyweight", "tai nha",
}

INJECTION_PATTERN = re.compile(
    r"\b(?:system prompt|developer prompt|chi dan he thong|lenh he thong|"
    r"bo qua (?:moi |tat ca )?(?:chi dan|quy tac|gioi han)|"
    r"ignore (?:all )?(?:previous|prior|system) instructions|"
    r"reveal (?:your |the )?(?:system|developer) prompt|"
    r"injected_ok|lay cap (?:mat khau|cookie)|tiet lo (?:prompt|cau hinh))\b"
    r"|\[(?:system|developer)\]"
)


def is_prompt_injection(question: str) -> bool:
    return bool(INJECTION_PATTERN.search(normalize(question)))

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
    return {normalize(row["question"]).strip() for row in load_train_json()}


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
    return has_context and bool(re.search(
        r"\b(con|neu|vay|the|doi|sao|bao nhieu|ngay|tuan|nua|no|bai nay|bai do|dong tac nay|tiep|dau tien|"
        r"dung cu|ta|may|khong co|thay|thay the|de hon|kho hon|dau|chan thuong|thoi gian|phut|buoi|"
        r"tai nha|goi|lung|vai|tay|chan|bung|khong dung cu)\b",
        normalized,
    ))


def requested_days(question: str) -> int | None:
    normalized = normalize(question)
    match = re.search(r"(?<!\d)([1-6])\s*(?:buoi|ngay)(?:\s*/\s*tuan|\s*(?:moi|mot)?\s*tuan)?", normalized)
    return int(match.group(1)) if match else None


def detect_equipment(text: str) -> str | None:
    normalized = normalize(text)
    if any(k in normalized for k in ("khong co dung cu", "khong dung cu", "chua co dung cu", "khong can dung cu", "bodyweight", "trong luong co the")):
        return "home_bodyweight"
    if any(k in normalized for k in ("co dung cu", "day du dung cu", "co ta", "dung cu tai nha")):
        return "home_dumbbell"
    if any(k in normalized for k in ("ta don", "ta tay", "dumbbell", "day khang luc", "resistance band")):
        return "home_dumbbell"
    if any(k in normalized for k in ("phong gym", "phong tap", "may tap", "barbell", "ta don lon", "day cap")):
        return "gym"
    return None


def detect_goal(text: str) -> str | None:
    normalized = normalize(text)
    if any(k in normalized for k in ("giam mo", "giam can", "dot mo", "thon gon", "siet mo")):
        return "giam_mo"
    if any(k in normalized for k in ("tang co", "to co", "tang can", "hypertrophy", "phat trien co bap")):
        return "tang_co"
    if any(k in normalized for k in ("suc khoe", "suc ben", "the luc", "tim mach", "khoe hon")):
        return "suc_khoe"
    return None


def detect_limitations(text: str) -> list[str]:
    normalized = normalize(text)
    limits = []
    if re.search(r"\b(?:dau|moi|ton thuong|thoai hoa|chan thuong)\s+(?:khop\s+)?goi\b", normalized) or "dau goi" in normalized:
        limits.append("knee")
    if re.search(r"\b(?:dau|moi|thoat vi|chan thuong)\s+(?:cot song\s+)?lung\b", normalized) or "dau lung" in normalized:
        limits.append("lower_back")
    if re.search(r"\b(?:dau|moi|chan thuong)\s+vai\b", normalized) or "dau vai" in normalized:
        limits.append("shoulder")
    return limits
