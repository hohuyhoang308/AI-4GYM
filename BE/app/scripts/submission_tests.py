"""Run software checks and persist per-case evidence for the submission report."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import platform
import subprocess
import time
import traceback
import unittest

from app.core.config import ROOT, settings


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = {}
        self.started = {}

    def row(self, test):
        return self.rows.setdefault(test.id(), {"test_id": test.id(),
            "description": test.shortDescription() or test.id().split(".")[-1],
            "status": "RUNNING", "details": []})

    def startTest(self, test):
        self.row(test)
        self.started[test.id()] = time.monotonic()
        super().startTest(test)

    def stopTest(self, test):
        self.row(test)["seconds"] = round(time.monotonic() - self.started[test.id()], 4)
        super().stopTest(test)

    def addSuccess(self, test):
        self.row(test)["status"] = "PASS"
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.row(test).update(status="FAIL")
        self.row(test)["details"].append(self._exc_info_to_string(err, test))
        super().addFailure(test, err)

    def addError(self, test, err):
        self.row(test).update(status="ERROR")
        self.row(test)["details"].append(self._exc_info_to_string(err, test))
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.row(test).update(status="SKIP", details=[reason])
        super().addSkip(test, reason)

    def addSubTest(self, test, subtest, err):
        if err:
            self.row(test)["status"] = "FAIL" if issubclass(err[0], AssertionError) else "ERROR"
            self.row(test)["details"].append(str(subtest) + "\n" + self._exc_info_to_string(err, test))
        super().addSubTest(test, subtest, err)


def run(output: Path, regressions_only=False, build=True):
    pattern = "test_submission_regressions.py" if regressions_only else "test_*.py"
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=pattern)
    log = io.StringIO()
    started = time.monotonic()
    result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=EvidenceResult).run(suite)
    cases = list(result.rows.values())
    report = {"created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "platform": platform.platform(), "python": platform.python_version(),
        "scope": "Regression tests only" if regressions_only else "Unit, HTTP integration, dataset/index and local MySQL/Ollama integration",
        "summary": {"tests_run": result.testsRun, "passed": sum(r["status"] == "PASS" for r in cases),
            "failed": sum(r["status"] == "FAIL" for r in cases), "errors": sum(r["status"] == "ERROR" for r in cases),
            "skipped": sum(r["status"] == "SKIP" for r in cases), "seconds": round(time.monotonic() - started, 3)},
        "cases": cases, "file_sha256": {}}
    for relative in ("app/services/chat.py", "app/services/plans.py", "app/services/scope.py",
                     "app/scripts/export_report.py", "tests/test_software.py", "tests/test_submission_regressions.py"):
        report["file_sha256"][relative] = sha256((ROOT / relative).read_bytes()).hexdigest()
    if not regressions_only:
        from app.scripts.audit_report import audit
        from app.services.index import vector_store
        from app.services.knowledge import build_documents
        try:
            report["artifact_audit"] = audit()
        except Exception:
            report["artifact_audit"] = {"status": "FAIL", "error": traceback.format_exc()}
        try:
            train = json.loads(settings.train_json_path.read_text(encoding="utf-8"))
            expected = {str(d.id): (d.page_content, d.metadata) for d in build_documents(train)}
            stored = vector_store().get(include=["documents", "metadatas"])
            actual = {key: (doc, meta) for key, doc, meta in zip(stored["ids"], stored["documents"], stored["metadatas"])}
            report["index_content_audit"] = {"status": "PASS" if actual == expected else "FAIL",
                "expected_documents": len(expected), "actual_documents": len(actual),
                "mismatched_ids": sorted(key for key in expected.keys() | actual.keys() if actual.get(key) != expected.get(key))}
        except Exception:
            report["index_content_audit"] = {"status": "ERROR", "error": traceback.format_exc()}
        if build:
            completed = subprocess.run(["npm.cmd", "run", "build"], cwd=ROOT.parent / "FE",
                                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            report["frontend_build"] = {"status": "PASS" if completed.returncode == 0 else "FAIL",
                "exit_code": completed.returncode, "log": completed.stdout + completed.stderr}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output.with_suffix(".txt").write_text(log.getvalue(), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "reports" / "results" / "software_test_results.json")
    parser.add_argument("--regressions-only", action="store_true")
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    report = run(args.output, args.regressions_only, not args.no_build)
    checks = [report["summary"]["failed"] == 0, report["summary"]["errors"] == 0,
              report.get("artifact_audit", {}).get("artifact_integrity", "PASS") == "PASS",
              report.get("index_content_audit", {}).get("status", "PASS") == "PASS",
              report.get("frontend_build", {}).get("status", "PASS") == "PASS"]
    raise SystemExit(0 if all(checks) else 1)
