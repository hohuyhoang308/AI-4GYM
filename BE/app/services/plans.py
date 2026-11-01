from app.services.knowledge import load_exercises


ACSM_SOURCE = "https://acsm.org/resistance-training-guidelines-update-2026/"

TEMPLATES = {
    1: ("Toàn thân", [(1, "Toàn thân A")]),
    2: ("Toàn thân", [(1, "Toàn thân A"), (4, "Toàn thân B")]),
    3: ("Toàn thân", [(1, "Toàn thân A"), (3, "Toàn thân B"), (5, "Toàn thân A")]),
    4: ("Upper/Lower", [(1, "Thân trên A"), (2, "Thân dưới A"), (4, "Thân trên B"), (5, "Thân dưới B")]),
    5: ("Upper/Lower + kỹ thuật", [(1, "Thân trên A"), (2, "Thân dưới A"), (4, "Thân trên B"), (5, "Thân dưới B"), (6, "Kỹ thuật nhẹ")]),
    6: ("Push/Pull/Legs", [(1, "Đẩy"), (2, "Kéo"), (3, "Chân"), (5, "Đẩy"), (6, "Kéo"), (7, "Chân")]),
}

GROUPS = {
    "Toàn thân A": ["bodyweight-squat", "bent-knee-push-up", "seated-row", "glute-bridge"],
    "Toàn thân B": ["leg-press", "chest-press", "lat-pulldown", "front-plank"],
    "Thân trên A": ["bent-knee-push-up", "seated-row", "shoulder-press", "bicep-curl"],
    "Thân trên B": ["chest-press", "lat-pulldown", "shoulder-press", "bicep-curl"],
    "Thân dưới A": ["bodyweight-squat", "glute-bridge", "front-plank"],
    "Thân dưới B": ["leg-press", "glute-bridge", "front-plank"],
    "Kỹ thuật nhẹ": ["bodyweight-squat", "bent-knee-push-up", "seated-row"],
    "Đẩy": ["chest-press", "shoulder-press", "bent-knee-push-up"],
    "Kéo": ["lat-pulldown", "seated-row", "bicep-curl"],
    "Chân": ["bodyweight-squat", "leg-press", "glute-bridge"],
}


def make_plan(days: int) -> dict:
    if days not in TEMPLATES:
        raise ValueError("Số ngày tập phải từ 1 đến 6")
    name, sequence = TEMPLATES[days]
    names = {exercise["id"]: exercise["name"] for exercise in load_exercises()}
    schedule = [
        {"weekday": weekday, "focus": focus, "exercises": [{"id": item, "name": names[item]} for item in GROUPS[focus]]}
        for weekday, focus in sequence
    ]
    note = "Người mới nên bắt đầu 2–3 buổi sức mạnh mỗi tuần, tập các nhóm cơ lớn và tăng dần theo khả năng."
    if days == 1:
        note = "Một buổi vẫn tốt để bắt đầu; nếu có thể, tăng dần lên ít nhất 2 buổi sức mạnh mỗi tuần."
    elif days >= 5:
        note = "Lịch này chỉ là mẫu tham khảo. Người mới có thể giảm xuống 2–4 buổi nếu khó hồi phục; ưu tiên kỹ thuật và nghỉ ngơi."
    return {"days_per_week": days, "split": name, "schedule": schedule, "guidance": "Chọn mức tập dễ kiểm soát, ưu tiên kỹ thuật và tăng dần theo khả năng. Khởi động trước buổi tập và dừng nếu đau bất thường.", "note": note, "source": ACSM_SOURCE}
