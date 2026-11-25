"""Verification script for Kỹ thuật 1 — AI Chatbot & Backend."""

import json
from pathlib import Path
import time
from app.services.chat import ChatService
from app.services.plans import make_plan


def main() -> None:
    service = ChatService()
    results = {}

    print("=== 1. KIỂM THỬ TRƯỚC / SAU: CÂU 214, 90, 371 ===")
    before_after = [
        {
            "id": "qa-214",
            "question": "Làm thế nào để thực hiện bài tập chèo thuyền gập người (bent-over row)?",
            "before": "Đứng với tạ ở tay trái, đặt ghế dài hoặc ghế tựa ở bên phải. Đặt tay và đầu gối phải lên ghế.\nLưu ý: Luôn khởi động kỹ trước khi tập và duy trì mức tạ vừa phải để đảm bảo an toàn.",
            "before_issue": "Chỉ mô tả tư thế chuẩn bị, thiếu pha kéo, co bả vai, hạ tạ và lỗi sai (Điểm 1/2).",
        },
        {
            "id": "qa-90",
            "question": "Trẻ em và thanh thiếu niên nên vận động thể chất ở mức độ như thế nào?",
            "before": "Theo Hướng dẫn Hoạt động Thể chất cho người Mỹ, trẻ em và thanh thiếu niên nên hướng tới ít nhất 150 phút hoạt động aerobic cường độ vừa phải hoặc 75 phút hoạt động aerobic cường độ mạnh mỗi tuần.",
            "before_issue": "Trả lời sai sang khuyến nghị 150 phút/tuần của người lớn; trẻ em cần ít nhất 60 phút mỗi ngày (Điểm 1/2).",
        },
        {
            "id": "qa-371",
            "question": "Tôi có thể tập thể dục trong thời gian nhịn ăn (ví dụ: tháng Ramadan) không?",
            "before": "Mình chỉ hỗ trợ tra cứu bài tập, nhóm cơ và gợi ý lịch tập Gym/Fitness. Bạn hãy hỏi về chủ đề này nhé.",
            "before_issue": "Bị chặn ngoài phạm vi (Refusal), từ chối trả lời (Điểm 0/2).",
        },
    ]

    evaluated_fixes = []
    for item in before_after:
        start = time.monotonic()
        reply = service.ask(item["question"])
        elapsed = round(time.monotonic() - start, 2)
        evaluated_fixes.append({
            "id": item["id"],
            "question": item["question"],
            "before": item["before"],
            "before_issue": item["before_issue"],
            "after": reply["answer"],
            "sources": [s["id"] for s in reply["sources"]],
            "refused": reply["refused"],
            "seconds": elapsed,
        })
        print(f"[{item['id']}] Hoàn thành trong {elapsed}s (Refused: {reply['refused']})")

    results["before_after_fixes"] = evaluated_fixes

    print("\n=== 2. KIỂM THỬ HỘI THOẠI NHIỀU LƯỢT (MULTI-TURN) ===")
    multi_turn_convo = []
    session_id = None
    turns = [
        "Tôi muốn tập chân tại nhà.",
        "Tôi không có dụng cụ.",
        "Tôi bị đau khớp gối thì sao?",
    ]
    for i, user_msg in enumerate(turns, 1):
        reply = service.ask(user_msg, session_id=session_id)
        session_id = reply["session_id"]
        multi_turn_convo.append({
            "turn": i,
            "user": user_msg,
            "bot": reply["answer"],
            "sources": [s["id"] for s in reply["sources"]],
        })
        print(f"Turn {i}: '{user_msg}' -> Trả lời {len(reply['answer'].splitlines())} dòng")

    results["multi_turn_convo"] = multi_turn_convo

    print("\n=== 3. KIỂM THỬ CÁ NHÂN HÓA VÀ HỎI BỔ SUNG CHỦ ĐỘNG ===")
    clarify_reply = service.ask("Tư vấn lịch tập cho tôi")
    results["proactive_clarification"] = {
        "user": "Tư vấn lịch tập cho tôi",
        "bot": clarify_reply["answer"],
    }

    # Test distinct profile plans
    results["personalized_profiles"] = {
        "profile_A_home_fatloss": make_plan(days=3, equipment="home_bodyweight", goal="giam_mo"),
        "profile_B_gym_hypertrophy": make_plan(days=4, equipment="gym", goal="tang_co"),
        "profile_C_knee_friendly": make_plan(days=3, equipment="home_bodyweight", limitations=["knee"], target_muscle="chan"),
    }

    output_path = Path(__file__).resolve().parents[3] / "reports" / "results" / "ky_thuat_1_evidence.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã lưu toàn bộ bằng chứng kiểm thử vào {output_path.resolve()}")


if __name__ == "__main__":
    main()
