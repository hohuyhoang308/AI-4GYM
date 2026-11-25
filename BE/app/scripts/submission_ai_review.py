"""Fresh local chatbot acceptance review; keeps historical 193-case artifacts intact."""

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
from urllib.request import urlopen

from app.core.config import ROOT, settings
from app.scripts.evaluate_chatbot import grade, make_judge
from app.services.chat import ChatService
from app.services.index import indexed_count


OUTPUT = ROOT.parent / "reports" / "results" / "chatbot_ai_review.json"
CASES = ROOT / "data" / "curated" / "submission_cases.json"


def contract(case, replies):
    last = replies[-1]
    text = last["answer"]
    expect = case["expect"]
    if expect == "refusal":
        return last["refused"] and not last["sources"]
    if last["refused"] or not text.strip():
        return False
    if expect == "rag":
        return bool(last["sources"])
    if expect == "clarification":
        return all(t in text for t in ("Thời gian", "Dụng cụ", "Mục tiêu", "Hạn chế"))
    if expect == "bodyweight":
        return "Lịch 3 buổi/tuần" in text and "Không dụng cụ" in text and "Mục tiêu tăng cơ" in text
    if expect == "knee_refinement":
        # Match scheduled exercise lines only; warnings may name excluded exercises.
        scheduled = "\n".join(line for line in text.splitlines() if line.startswith("- "))
        return ("Lịch 3 buổi/tuần" in text and "Không dụng cụ" in text
                and "Squat" not in scheduled and "Đạp chân" not in scheduled
                and ("bác sĩ" in text or "y tế" in text))
    if expect == "shoulder":
        return "Đẩy vai" not in text and ("bác sĩ" in text or "y tế" in text)
    if expect == "latest_constraints":
        return all(t in text for t in ("Lịch 4 buổi/tuần", "Tạ đơn", "Mục tiêu tăng cơ")) and "Không dụng cụ" not in text and "Mục tiêu giảm mỡ" not in text
    raise ValueError(expect)


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    with urlopen(settings.ollama_base_url + "/api/tags", timeout=5) as response:
        models = {m["name"]: m["digest"] for m in json.load(response)["models"]}
    service, judge = ChatService(), make_judge()
    report = {"created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "platform": platform.platform(), "python": platform.python_version(),
        "chat_model": settings.chat_model, "embed_model": settings.embed_model,
        "chat_model_digest": models.get(settings.chat_model), "embed_model_digest": models.get(settings.embed_model),
        "indexed_documents": indexed_count(), "case_file_sha256": sha256(CASES.read_bytes()).hexdigest(),
        "source_sha256": sha256(settings.excel_path.read_bytes()).hexdigest(),
        "code_sha256": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in
            [ROOT / "app/services" / n for n in ("chat.py", "plans.py", "scope.py")]},
        "method": "12 acceptance scenarios / 16 user turns. Fresh ChatService answers; local Qwen judge v3, separate chatbot/judge latency. Designed for regression and smoke checks, not an unbiased held-out accuracy estimate. Same model family generates and grades; independent textual review is in the submission report.",
        "cases": []}
    for case in cases:
        rows, replies, session_id = [], [], None
        error = None
        for turn, message in enumerate(case["messages"], 1):
            start = time.monotonic()
            try:
                reply = service.ask(message, session_id=session_id)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                rows.append({"turn": turn, "message": message, "error": error,
                             "chatbot_seconds": round(time.monotonic() - start, 3)})
                break
            session_id = reply["session_id"]
            replies.append(reply)
            rows.append({"turn": turn, "message": message, **reply,
                         "chatbot_seconds": round(time.monotonic() - start, 3)})
        result = {**case, "turns": rows, "error": error,
                  "contract_passed": not error and contract(case, replies)}
        if not error:
            start = time.monotonic()
            try:
                question = "\n".join(f"Lượt {i}: {message}" for i, message in enumerate(case["messages"], 1))
                score, reason = grade(judge, question, case["reference"], replies[-1]["answer"])
                result.update(judge_score=score, judge_reason=reason, judge_version=3)
            except Exception as exc:
                result.update(judge_score=None, judge_error=f"{type(exc).__name__}: {exc}")
            result["judge_seconds"] = round(time.monotonic() - start, 3)
        report["cases"].append(result)
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{case['id']}: contract={result['contract_passed']}, judge={result.get('judge_score')}, chatbot={sum(r['chatbot_seconds'] for r in rows):.3f}s", flush=True)
    times = [row["chatbot_seconds"] for case in report["cases"] for row in case["turns"] if "error" not in row]
    rag_times = [row["chatbot_seconds"] for case in report["cases"] if case["expect"] == "rag" for row in case["turns"] if "error" not in row]
    report["summary"] = {"scenarios": len(report["cases"]), "user_turns": len(times),
        "contract_passed": sum(c["contract_passed"] for c in report["cases"]),
        "judge_scores": dict(Counter(c.get("judge_score") for c in report["cases"])),
        "errors": sum(bool(c["error"]) for c in report["cases"]),
        "judge_errors": sum(bool(c.get("judge_error")) for c in report["cases"]),
        "rag_turns": len(rag_times), "rag_mean_seconds": round(statistics.mean(rag_times), 3) if rag_times else None,
        "rag_median_seconds": round(statistics.median(rag_times), 3) if rag_times else None,
        "rag_min_seconds": min(rag_times) if rag_times else None, "rag_max_seconds": max(rag_times) if rag_times else None}
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
