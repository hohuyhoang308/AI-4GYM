from app.services.knowledge import load_exercises


# Trang tóm tắt Position Stand 2026 của ACSM về tập sức mạnh. Các lịch bên dưới là mẫu do
# nhóm biên soạn, chỉ THAM KHẢO nguyên tắc chung của ACSM, không phải lịch "chuẩn ACSM".
ACSM_SOURCE = "https://acsm.org/resistance-training-guidelines-update-2026/"

# Bài có chuyển động kéo (lưng xô, lưng giữa, tay trước).
PULL_EXERCISES = {"lat-pulldown", "seated-row", "bent-over-row", "bicep-curl"}

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


EQUIPMENT_BODYWEIGHT_MAP = {
    "leg-press": "bodyweight-squat",
    "chest-press": "bent-knee-push-up",
    "lat-pulldown": "front-plank",
    "seated-row": "glute-bridge",
    "shoulder-press": "bent-knee-push-up",
    "bicep-curl": "front-plank",
}

EQUIPMENT_DUMBBELL_MAP = {
    "lat-pulldown": "bent-over-row",
    "seated-row": "bent-over-row",
    "leg-press": "bodyweight-squat",
    "chest-press": "bent-knee-push-up",
    "shoulder-press": "bent-knee-push-up",
    "bicep-curl": "bent-over-row",
}


def make_plan(
    days: int = 3,
    equipment: str | None = None,
    goal: str | None = None,
    limitations: list[str] | None = None,
    target_muscle: str | None = None,
) -> dict:
    if days not in TEMPLATES:
        days = max(1, min(days, 6)) if days else 3

    name, sequence = TEMPLATES[days]
    exercises_map = {exercise["id"]: exercise for exercise in load_exercises()}
    limitations = limitations or []

    def resolve_exercise_id(ex_id: str) -> str:
        res = ex_id
        if equipment == "home_bodyweight":
            res = EQUIPMENT_BODYWEIGHT_MAP.get(res, res)
        elif equipment == "home_dumbbell":
            res = EQUIPMENT_DUMBBELL_MAP.get(res, res)

        if "knee" in limitations:
            if res == "bodyweight-squat":
                res = "glute-bridge"
            elif res == "leg-press":
                res = "front-plank"
        if "lower_back" in limitations and res in ("seated-row", "bent-over-row"):
            res = "front-plank"
        return res if res in exercises_map else "front-plank"

    schedule = []
    pull_substituted = False
    for weekday, focus in sequence:
        raw_items = GROUPS.get(focus, GROUPS["Toàn thân A"])
        if target_muscle == "chan":
            raw_items = ["bodyweight-squat", "leg-press", "glute-bridge"]
        elif target_muscle in ("nguc", "tay", "vai"):
            raw_items = ["bent-knee-push-up", "chest-press", "shoulder-press", "bicep-curl"]
        elif target_muscle == "lung":
            raw_items = ["seated-row", "lat-pulldown", "bent-over-row"]

        resolved_ids = []
        day_lost_pull = False
        for item in raw_items:
            resolved = resolve_exercise_id(item)
            if item in PULL_EXERCISES and resolved not in PULL_EXERCISES:
                day_lost_pull = True
            if resolved not in resolved_ids:
                resolved_ids.append(resolved)
        pull_substituted = pull_substituted or day_lost_pull

        day_focus = f"{focus} (Chân)" if target_muscle == "chan" else focus
        if day_lost_pull and not any(item in PULL_EXERCISES for item in resolved_ids) and (focus == "Kéo" or target_muscle == "lung"):
            # Không còn bài kéo thật: đổi tên buổi cho trung thực thay vì vẫn gọi là "Kéo"/"Lưng".
            day_focus = f"{day_focus} → Core & chuỗi sau (thiếu dụng cụ kéo)"

        schedule.append({
            "weekday": weekday,
            "focus": day_focus,
            "exercises": [{"id": item, "name": exercises_map[item]["name"]} for item in resolved_ids],
        })

    guidance_parts = [
        "Chọn mức tập dễ kiểm soát, ưu tiên kỹ thuật và tăng dần theo khả năng.",
        "Khởi động trước buổi tập và dừng nếu đau bất thường.",
    ]
    if equipment == "home_bodyweight":
        name = f"{name} (Tại nhà - Không dụng cụ)"
        guidance_parts.append("Các bài tập được thiết kế hoàn toàn bằng trọng lượng cơ thể (Bodyweight), không cần tạ hay máy tập.")
    elif equipment == "home_dumbbell":
        name = f"{name} (Tại nhà - Tạ đơn)"
        guidance_parts.append("Lịch tập kết hợp tạ đơn, ghế tựa chắc chắn và các bài trọng lượng cơ thể; không yêu cầu máy tập hoặc dây kháng lực.")

    if pull_substituted:
        guidance_parts.append(
            "Thiếu dụng cụ nên một số bài kéo (kéo xô, chèo, cuốn tay) đã được thay bằng bài core/mông; "
            "lịch vì vậy thiếu cân bằng đẩy–kéo. Nên bổ sung dây kháng lực hoặc tạ đơn để tập chèo (row) cho lưng."
        )

    if goal == "giam_mo":
        guidance_parts.append("Mục tiêu giảm mỡ: Kết hợp các bài sức mạnh này với tối thiểu 150 phút vận động thể chất/aerobic vừa phải mỗi tuần.")
    elif goal == "tang_co":
        guidance_parts.append("Mục tiêu tăng cơ: Áp dụng nguyên tắc quá tải tiến triển và bổ sung đủ dinh dưỡng protein.")

    if "knee" in limitations:
        guidance_parts.append("Lưu ý khớp gối: Mẫu đã loại squat và đạp chân, nhưng không bảo đảm phù hợp với mọi chấn thương. Dừng động tác gây đau và tham khảo bác sĩ hoặc chuyên gia y tế trước khi tập tiếp.")
    if "lower_back" in limitations:
        guidance_parts.append("Lưu ý lưng dưới: Tránh các chuyển động vặn gập lưng nặng. Dừng động tác gây đau và tham khảo bác sĩ hoặc chuyên gia y tế; đây không phải lịch phục hồi chấn thương.")

    note = "Người mới nên bắt đầu 2–3 buổi sức mạnh mỗi tuần, tập các nhóm cơ lớn và tăng dần theo khả năng."
    if days == 1:
        note = "Một buổi vẫn tốt để bắt đầu; nếu có thể, tăng dần lên ít nhất 2 buổi sức mạnh mỗi tuần."
    elif days >= 5:
        note = "Lịch này chỉ là mẫu tham khảo. Người mới có thể giảm xuống 2–4 buổi nếu khó hồi phục; ưu tiên kỹ thuật và nghỉ ngơi."

    return {
        "days_per_week": days,
        "split": name,
        "schedule": schedule,
        "guidance": " ".join(guidance_parts),
        "note": note,
        "source": ACSM_SOURCE,
    }
