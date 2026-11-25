"""Validate finalized documents and package only submission artifacts, not secrets."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

import pymupdf as fitz
from openpyxl import load_workbook
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
EVIDENCE = REPORTS / "evidence"
RESULTS = REPORTS / "results"
PREVIEWS = ROOT / ".local" / "report-preview"
PREVIEWS.mkdir(parents=True, exist_ok=True)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


software = read("software_test_results.json")
assert software["summary"]["passed"] == 53
assert len({c["test_id"] for c in software["cases"]}) == 53
for name, expected in software["file_sha256"].items():
    assert digest(ROOT / "BE" / name) == expected, name
assert digest(RESULTS / "chatbot_ai_review.json") == read("independent_ai_review.json")["reviewed_artifact_sha256"]
assert len(read("browser_test_results.json")["cases"]) == 10
assert all(c["status"] == "PASS" for c in read("browser_test_results.json")["cases"])

validation = {}
for name in ["Tieu_luan_AI_4GYM_CT07PM", "Bao_cao_kiem_thu_AI_4GYM"]:
    pdf = fitz.open(REPORTS / (name + ".pdf"))
    texts = [page.get_text() for page in pdf]
    text = "\n\n".join(texts)
    assert len(pdf) > 0, name + ": empty document"
    assert all(len(t.strip()) >= 100 for t in texts), name + ": blank page"
    evidence_text = re.sub(r"\s+", "", text)
    assert "53/53" in evidence_text and "AI-12" in evidence_text and any(value in evidence_text for value in ("85.205", "85,205")), name
    if name.startswith("Tieu"):
        assert "MỤC LỤC" in text
    (PREVIEWS / (name + "_extracted.txt")).write_text(text, encoding="utf-8")
    for start in range(0, len(pdf), 12):
        canvas = Image.new("RGB", (1000, 1120), "#dddddd")
        draw = ImageDraw.Draw(canvas)
        for i in range(start, min(start + 12, len(pdf))):
            pix = pdf[i].get_pixmap(matrix=fitz.Matrix(.45, .45))
            im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            im.thumbnail((240, 335))
            x, y = ((i - start) % 4) * 250 + 5, ((i - start) // 4) * 370 + 20
            canvas.paste(im, (x, y))
            draw.text((x, y - 15), f"Page {i + 1}", fill="black")
        canvas.save(PREVIEWS / f"{name}_preview_{start + 1}.png")
    validation[name] = {"pages": len(pdf), "text_characters": len(text), "blank_pages": [], "required_evidence_text": "PASS"}

workbook = load_workbook(REPORTS / "Bo_kiem_thu_AI_4GYM.xlsx", read_only=True, data_only=True)
expected_rows = {"Ca phan mem": 54, "Chatbot AI moi": 13, "Tung luot chatbot": 17, "193 cau ban giao": 194}
for name, rows in expected_rows.items():
    assert workbook[name].max_row == rows, (name, workbook[name].max_row)
validation["workbook"] = {sheet.title: {"rows": sheet.max_row, "columns": sheet.max_column} for sheet in workbook}
workbook.close()
historical = ["reports/evaluation_results.jsonl", "reports/AI-4GYM_train_test_report.xlsx"]
for path in historical:
    # Respect Git's CRLF checkout conversion on Windows.
    original_blob = subprocess.check_output(["git", "rev-parse", "HEAD:" + path], cwd=ROOT).strip()
    current_blob = subprocess.check_output(["git", "hash-object", "--path=" + path, path], cwd=ROOT).strip()
    assert original_blob == current_blob, path
validation["source_hashes"] = "PASS"
validation["historical_artifacts_unchanged"] = True
(EVIDENCE / "document_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

names = [
    "Tieu_luan_AI_4GYM_CT07PM.docx", "Tieu_luan_AI_4GYM_CT07PM.pdf",
    "Bao_cao_kiem_thu_AI_4GYM.docx", "Bao_cao_kiem_thu_AI_4GYM.pdf",
    "Bo_kiem_thu_AI_4GYM.xlsx", "HO_SO_NOP.md", "README.md", "results/AI_REVIEW_NHAN_XET.md",
    "results/software_test_results.json", "results/software_test_results.txt", "results/browser_test_results.json",
    "results/chatbot_ai_review.json", "results/independent_ai_review.json", "results/regressions_before.json",
    "results/regressions_before.txt", "results/regressions_after.json", "results/regressions_after.txt",
    "requirements-report.txt", "evaluation_results.jsonl", "AI-4GYM_train_test_report.xlsx",
]
paths = [REPORTS / name for name in names]
paths += [p for p in EVIDENCE.iterdir() if p.is_file()]
paths += [p for p in (REPORTS / "tools").iterdir() if p.is_file()]
paths += [ROOT / "BE" / name for name in software["file_sha256"]]
paths += [ROOT / name for name in [
    "README.md", "docs/setup.md", "docs/project-structure.md", "docs/report-review.md",
    "reports/releases/README.md",
    "reports/history/SECURITY_PERFORMANCE.md", "BE/data/processed/split_manifest.json",
    "BE/app/scripts/submission_tests.py", "BE/app/scripts/submission_ai_review.py",
    "BE/data/curated/submission_cases.json",
]]
# Include all existing test modules referenced by the 53-case result, not only new tests.
paths += list((ROOT / "BE" / "tests").glob("*.py"))
paths = sorted(set(paths))
manifest = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "test_base_commit": software["git_commit"],
    "version_note": "Test evidence predates the cleanup commit. Source hashes bind the tested fixes; result files were moved without rewriting outcomes. Refer to Git history for the publication commit.",
    "validation": validation,
    "files": {p.relative_to(ROOT).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size} for p in paths},
}
manifest_path = REPORTS / "submission_manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
archive = REPORTS / "releases" / "AI_4GYM_HO_SO_NOP_CT07PM.zip"
archive.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(archive, "w", ZIP_DEFLATED) as z:
    for path in paths + [manifest_path]:
        z.write(path, path.relative_to(ROOT).as_posix())
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert not any(Path(n).name == ".env" for n in z.namelist())
    for path, expected in manifest["files"].items():
        assert sha256(z.read(path)).hexdigest() == expected["sha256"], path
print(json.dumps({"validation": validation, "archive": str(archive), "archive_bytes": archive.stat().st_size,
                  "archive_sha256": digest(archive), "files": len(paths) + 1}, ensure_ascii=False, indent=2))
