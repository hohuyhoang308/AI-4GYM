"""Chạy toàn bộ unittest và lưu minh chứng vào reports/results/.

Cách dùng (tại BE/):
    python -m app.scripts.run_tests

Tạo hai tệp software_test_results_<YYYYMMDD>.json và .txt, ghi rõ nền tảng, phiên bản
Python, commit Git, số ca đạt/lỗi/bỏ qua và lý do bỏ qua của từng ca.
"""

from datetime import datetime, timezone
import io
import json
import platform
import subprocess
import sys
import time
import unittest

from app.core.config import ROOT


RESULTS_DIR = ROOT.parent / "reports" / "results"


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cases: list[dict] = []

    def _record(self, test: unittest.TestCase, status: str, detail: str = "") -> None:
        self.cases.append({
            "test_id": test.id(),
            "description": (test.shortDescription() or "").strip(),
            "status": status,
            "detail": detail.strip().splitlines()[-1] if detail else "",
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "fail", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT / "tests"))
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordingResult)
    started = time.perf_counter()
    result = runner.run(suite)
    seconds = round(time.perf_counter() - started, 3)

    counts = {status: sum(case["status"] == status for case in result.cases) for status in ("pass", "fail", "error", "skipped")}
    now = datetime.now(timezone.utc)
    report = {
        "created_at": now.isoformat(),
        "git_commit": _git_commit(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "scope": "Toàn bộ BE/tests: unit, HTTP với SQLite cô lập, dữ liệu/chỉ mục; ca tích hợp tự bỏ qua khi thiếu MySQL/Ollama",
        "summary": {"tests_run": result.testsRun, "passed": counts["pass"], "failed": counts["fail"],
                    "errors": counts["error"], "skipped": counts["skipped"], "seconds": seconds},
        "cases": result.cases,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = RESULTS_DIR / f"software_test_results_{now:%Y%m%d}"
    with stem.with_suffix(".json").open("w", encoding="utf-8", newline="\r\n") as output:
        output.write(json.dumps(report, ensure_ascii=False, indent=2))
    with stem.with_suffix(".txt").open("w", encoding="utf-8", newline="\r\n") as output:
        output.write(stream.getvalue())
    summary = report["summary"]
    print(f"Ran {summary['tests_run']}: {summary['passed']} pass, {summary['failed']} fail, "
          f"{summary['errors']} error, {summary['skipped']} skipped -> {stem.with_suffix('.json')}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
