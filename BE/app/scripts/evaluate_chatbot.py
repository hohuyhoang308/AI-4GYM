"""Run the real local chatbot on every held-out question and grade its answers."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.core.config import ROOT, settings
from app.scripts.export_report import export_report, load_verified_data
from app.services.chat import ChatService
from app.services.knowledge import normalize


DEFAULT_RESULTS = ROOT.parent / "reports" / "evaluation_results.jsonl"
JUDGE_VERSION = 3
JUDGE_PROMPT = """Bạn là người chấm độc lập cho câu hỏi Gym/Fitness. So sánh CÂU TRẢ LỜI CHATBOT với ĐÁP ÁN THAM CHIẾU cho đúng CÂU HỎI.
Chỉ dùng đáp án tham chiếu làm chuẩn. Diễn đạt khác vẫn đúng. Để được 2 điểm, câu trả lời phải bao quát đầy đủ các ý chính mà câu hỏi yêu cầu, không mâu thuẫn và không chứa chỉ dẫn nguy hiểm. Nếu câu hỏi yêu cầu nhiều bài tập/cách làm mà chatbot chỉ nêu một, cho tối đa 1 điểm. Nếu đáp án tham chiếu nêu nhiều bước hoặc điều kiện quan trọng mà chatbot bỏ qua, cho tối đa 1 điểm. Kiểm tra các con số và đơn vị bắt buộc: lịch 3–5 buổi, mỗi buổi 20–30 phút không đảm bảo tối thiểu 150 phút vận động/tuần; chỉ cho tối đa 1 điểm nếu đáp án chuẩn yêu cầu ngưỡng này.
Cho điểm: 2 = đủ ý chính và đúng; 1 = đúng một phần nhưng thiếu ý quan trọng hoặc quá chung; 0 = sai, từ chối, không trả lời hoặc mâu thuẫn đáng kể. Chấm nghiêm khắc; không cho 2 chỉ vì có một ví dụ đúng.
Trả về duy nhất JSON với khóa score (số nguyên 0, 1 hoặc 2) và reason (tối đa 20 từ tiếng Việt)."""


def token_f1(reference: str, prediction: str) -> float:
    from collections import Counter

    reference_tokens = normalize(reference).split()
    prediction_tokens = normalize(prediction).split()
    if not reference_tokens or not prediction_tokens:
        return 0.0
    overlap = sum((Counter(reference_tokens) & Counter(prediction_tokens)).values())
    precision = overlap / len(prediction_tokens)
    recall = overlap / len(reference_tokens)
    return round(2 * precision * recall / (precision + recall), 4) if overlap else 0.0


def rouge_l_f1(reference: str, prediction: str) -> float:
    reference_tokens = normalize(reference).split()
    prediction_tokens = normalize(prediction).split()
    if not reference_tokens or not prediction_tokens:
        return 0.0
    previous = [0] * (len(prediction_tokens) + 1)
    for reference_token in reference_tokens:
        current = [0]
        for position, prediction_token in enumerate(prediction_tokens, 1):
            current.append(previous[position - 1] + 1 if reference_token == prediction_token else max(previous[position], current[-1]))
        previous = current
    overlap = previous[-1]
    precision = overlap / len(prediction_tokens)
    recall = overlap / len(reference_tokens)
    return round(2 * precision * recall / (precision + recall), 4) if overlap else 0.0


def make_judge() -> ChatOllama:
    return ChatOllama(
        model=settings.chat_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        num_ctx=2048,
        num_predict=220,
        format="json",
    )


def required_condition_cap(reference: str, answer: str) -> tuple[int, str | None]:
    """Deterministic guard for a mandatory 150-minute weekly activity target."""
    ref = normalize(reference)
    activity_terms = ("cardio", "aerobic", "hoat dong the chat", "tap the duc")
    if not (re.search(r"\b150\s*phut\b", ref) and "tuan" in ref and any(term in ref for term in activity_terms)):
        return 2, None
    response = normalize(answer)
    if re.search(r"\b(?:150|1[6-9]\d|[2-9]\d\d)\s*phut\b", response) and "tuan" in response:
        return 2, None
    # A range guarantees the target only when both minimum days and minimum minutes reach it.
    schedules = re.findall(r"(\d+)\s*(?:[-–]\s*\d+)?\s*(?:buoi|ngay)[^.!?\n]{0,80}?(\d+)\s*(?:[-–]\s*\d+)?\s*phut", response)
    if any(int(days) * int(minutes) >= 150 for days, minutes in schedules):
        return 2, None
    return 1, "Thiếu bảo đảm tối thiểu 150 phút vận động mỗi tuần"


def grade(judge: ChatOllama, question: str, reference: str, answer: str) -> tuple[int, str]:
    payload = f"CÂU HỎI:\n{question}\n\nĐÁP ÁN THAM CHIẾU:\n{reference}\n\nCÂU TRẢ LỜI CHATBOT:\n{answer}"
    response = judge.invoke([SystemMessage(content=JUDGE_PROMPT), HumanMessage(content=payload)])
    content = str(response.content).strip()
    parsed = json.loads(content)
    score = parsed.get("score")
    reason = parsed.get("reason")
    if type(score) is not int or score not in (0, 1, 2) or not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"Kết quả chấm không hợp lệ: {content[:200]}")
    cap, required_reason = required_condition_cap(reference, answer)
    if score > cap:
        return cap, f"{required_reason}; AI: {reason.strip()}"
    return score, reason.strip()


def read_results(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    results = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row.get("id"), str):
            raise ValueError(f"Thiếu ID trong {path}, dòng {line_number}")
        results[row["id"]] = row
    return results


def compact_results(path: Path, ordered_rows: list[dict], results: dict[str, dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as output:
        for row in ordered_rows:
            output.write(json.dumps(results[row["id"]], ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def run(results_path: Path, limit: int | None = None, ids: set[str] | None = None) -> None:
    _, _, test_rows, manifest, _, _ = load_verified_data()
    test_hash = sha256(settings.test_json_path.read_bytes()).hexdigest()
    existing = read_results(results_path)
    if set(existing) - {row["id"] for row in test_rows}:
        raise ValueError("File kết quả có ID ngoài tập test")
    for result in existing.values():
        if result.get("test_sha256") != test_hash or result.get("chat_model") != settings.chat_model:
            raise ValueError("Dữ liệu test hoặc model đã thay đổi; đổi tên/xóa file kết quả cũ trước khi chạy lại")

    chatbot = ChatService()
    judge = make_judge()
    results_path.parent.mkdir(parents=True, exist_ok=True)
    selected = [row for row in test_rows if row["id"] in ids] if ids is not None else (test_rows[:limit] if limit else test_rows)
    if ids is not None and len(selected) != len(ids):
        raise ValueError(f"ID không thuộc tập test: {sorted(ids - {row['id'] for row in selected})}")
    for position, row in enumerate(selected, 1):
        prior = existing.get(row["id"])
        if prior and prior.get("judge_version") == JUDGE_VERSION:
            continue
        start = time.monotonic()
        if prior:
            reply = {"answer": prior["answer"], "sources": prior["sources"], "refused": prior["refused"]}
            answer_seconds = prior["seconds"]
            seconds_measurement = prior.get("seconds_measurement", "legacy_unknown_includes_judge_possibly")
        else:
            for attempt in range(3):
                try:
                    reply = chatbot.ask(row["question"], history_override=[])
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(3 * (attempt + 1))
            answer_seconds = round(time.monotonic() - start, 3)
            seconds_measurement = "chatbot_only"
            checkpoint = {
                "id": row["id"],
                "test_sha256": test_hash,
                "source_sha256": manifest["source_sha256"],
                "chat_model": settings.chat_model,
                "embed_model": settings.embed_model,
                "answer": reply["answer"],
                "sources": reply["sources"],
                "refused": reply["refused"],
                "judge_score": None,
                "judge_version": None,
                "seconds": answer_seconds,
                "seconds_measurement": seconds_measurement,
            }
            with results_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(checkpoint, ensure_ascii=False) + "\n")
                output.flush()
        for attempt in range(3):
            try:
                score, reason = grade(judge, row["question"], row["answer"], reply["answer"])
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3 * (attempt + 1))
        result = {
            "id": row["id"],
            "test_sha256": test_hash,
            "source_sha256": manifest["source_sha256"],
            "chat_model": settings.chat_model,
            "embed_model": settings.embed_model,
            "answer": reply["answer"],
            "sources": reply["sources"],
            "refused": reply["refused"],
            "judge_score": score,
            "judge_reason": reason,
            "judge_version": JUDGE_VERSION,
            "token_f1": token_f1(row["answer"], reply["answer"]),
            "rouge_l_f1": rouge_l_f1(row["answer"], reply["answer"]),
            "seconds": answer_seconds,
            "seconds_measurement": seconds_measurement,
        }
        with results_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
            output.flush()
        existing[row["id"]] = result
        print(f"[{position}/{len(selected)}] {row['id']}  judge={score}  {result['seconds']}s", flush=True)
    compact_results(results_path, [row for row in test_rows if row["id"] in existing], existing)
    export_report(results_path=results_path)
    print(f"Exported {len(existing)}/{len(test_rows)} test answers to Excel.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Đánh giá chatbot local trên tập test và xuất báo cáo Excel")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--limit", type=int, default=None, help="Chỉ chạy N câu đầu để kiểm thử; mặc định toàn bộ 193 câu")
    parser.add_argument("--ids", help="Danh sách ID test cách nhau bằng dấu phẩy, ví dụ qa-20,qa-42")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit phải lớn hơn 0")
    run(args.results, args.limit, set(args.ids.split(",")) if args.ids else None)


if __name__ == "__main__":
    main()
