"""Build the final submission from repository files using only the standard library."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "releases" / "AI-4GYM_FINAL.zip"
EXCLUDED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".local", "dist"}


def main() -> None:
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode("utf-8").split("\0")
    candidates = sorted(set(filter(None, names)))
    # --cached also returns tracked paths that have since become ignored.
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"],
        input="\0".join(candidates).encode("utf-8") + b"\0",
        cwd=ROOT, stdout=subprocess.PIPE, check=False,
    )
    if ignored.returncode not in (0, 1):
        raise RuntimeError("Cannot inspect ignored files")
    ignored_names = set(ignored.stdout.decode("utf-8").split("\0"))
    files = []
    for name in candidates:
        path = ROOT / name
        if name in ignored_names or not path.is_file() or path.suffix.lower() == ".zip":
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Invalid submission path: {name}")
        if EXCLUDED.intersection(path.relative_to(ROOT).parts):
            raise ValueError(f"Local artifact in submission: {name}")
        if path.name.startswith(".env") and path.name != ".env.example":
            raise ValueError(f"Local configuration in submission: {name}")
        files.append(path)
    required = {
        "README.md", "BE/.env.example", "BE/requirements.txt", "BE/app/main.py",
        "BE/data/raw/data.xlsx", "BE/data/processed/train.json",
        "BE/data/processed/test.json", "BE/data/curated/exercises.json",
        "FE/package.json", "FE/package-lock.json", "FE/src/App.tsx",
        "reports/Tieu_luan_AI_4GYM_CT07PM.pdf", "reports/Bao_cao_kiem_thu_AI_4GYM.pdf",
        "reports/Bo_kiem_thu_AI_4GYM.xlsx", "reports/AI-4GYM_train_test_report.xlsx",
        "reports/evaluation_results.jsonl",
    }
    relative_names = {p.relative_to(ROOT).as_posix() for p in files}
    if missing := required - relative_names:
        raise ValueError(f"Missing submission files: {sorted(missing)}")
    manifest = {
        p.relative_to(ROOT).as_posix(): {
            "sha256": sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size,
        } for p in files
    }
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, "AI-4GYM/" + path.relative_to(ROOT).as_posix())
        archive.writestr("AI-4GYM/submission_manifest.json", json.dumps(manifest, indent=2) + "\n")
    with ZipFile(ARCHIVE) as archive:
        if bad_file := archive.testzip():
            raise ValueError(f"Corrupt archive entry: {bad_file}")
        for name, expected in manifest.items():
            if sha256(archive.read("AI-4GYM/" + name)).hexdigest() != expected["sha256"]:
                raise ValueError(f"Archive hash mismatch: {name}")
    print(f"{ARCHIVE.relative_to(ROOT)}: {len(files)} files, {ARCHIVE.stat().st_size:,} bytes; integrity PASS")


if __name__ == "__main__":
    main()
