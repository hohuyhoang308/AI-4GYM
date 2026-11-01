"""Run the real local chatbot on every held-out question and grade its answers."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.core.config import ROOT, settings
from app.scripts.export_report import export_report, load_verified_data
from app.services.chat import ChatService
from app.services.knowledge import normalize


DEFAULT_RESULTS = ROOT.parent / "reports" / "evaluation_results.jsonl"
JUDGE_VERSION = 2
JUDGE_PROMPT = """Bạn là người chấm độc lập cho câu hỏi Gym/Fitness. So sánh CÂU TRẢ LỜI CHATBOT với ĐÁP ÁN THAM CHIẾU cho đúng CÂU HỎI.
Chỉ dùng đáp án tham chiếu làm chuẩn. Diễn đạt khác vẫn đúng. Để được 2 điểm, câu trả lời phải bao quát đầy đủ các ý chính mà câu hỏi yêu cầu, không mâu thuẫn và không chứa chỉ dẫn nguy hiểm. Nếu câu hỏi yêu cầu nhiều bài tập/cách làm mà chatbot chỉ nêu một, cho tối đa 1 điểm. Nếu đáp án tham chiếu nêu nhiều bước hoặc điều kiện quan trọng mà chatbot bỏ qua, cho tối đa 1 điểm.
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


def grade(judge: ChatOllama, question: str, reference: str, answer: str) -> tuple[int, str]:
    payload = f"CÂU HỎI:\n{question}\n\nĐÁP ÁN THAM CHIẾU:\n{reference}\n\nCÂU TRẢ LỜI CHATBOT:\n{answer}"
    response = judge.invoke([SystemMessage(content=JUDGE_PROMPT), HumanMessage(content=payload)])
    content = str(response.content).strip()
    parsed = json.loads(content)
    score = parsed.get("score")
    reason = parsed.get("reason")
    if type(score) is not int or score not in (0, 1, 2) or not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"Kết quả chấm không hợp lệ: {content[:200]}")
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


def run(results_path: Path, limit: int | None = None) -> None:
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
    selected = test_rows[:limit] if limit else test_rows
    for position, row in enumerate(selected, 1):
        prior = existing.get(row["id"])
        if prior and prior.get("judge_version") == JUDGE_VERSION:
            continue
        start = time.monotonic()
        if prior:
            reply = {"answer": prior["answer"], "sources": prior["sources"], "refused": prior["refused"]}
        else:
            for attempt in range(3):
                try:
                    reply = chatbot.ask(row["question"], history_override=[])
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(3 * (attempt + 1))
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
                "seconds": round(time.monotonic() - start, 1),
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
            "seconds": prior["seconds"] if prior else round(time.monotonic() - start, 1),
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
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit phải lớn hơn 0")
    run(args.results, args.limit)


if __name__ == "__main__":
    main()
