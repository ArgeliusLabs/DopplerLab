"""Build explicit-allowlist source and student archives; no private review data."""

import hashlib
import json
import zipfile
from pathlib import Path

from doppler_lab import __version__

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = [
    "README.md",
    "START_HERE.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "pyproject.toml",
    "MANIFEST.in",
    ".gitignore",
    ".gitattributes",
    "requirements-tested-win-py313.txt",
]
PATTERNS = [
    "src/**/*.py",
    "tests/**/*.py",
    "scripts/**/*.py",
    "docs/*.md",
    "assets/*.png",
    "assets/*.svg",
    "examples/**/*.json",
    "examples/**/*.csv",
    "examples/**/*.wav",
    "examples/**/*.html",
    "examples/**/*.png",
    "examples/**/*.md",
    ".github/**/*.yml",
    ".github/**/*.md",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_zip(path, files, prefix):
    # Explicit source inventory excludes work/, .tmp/, .venv/ and local-review/.
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in sorted(files):
            relative = item.relative_to(ROOT)
            if any(
                part in {"__pycache__", ".venv", ".tmp", "local-review", "work"}
                for part in relative.parts
            ):
                raise ValueError(
                    f"Unexpected private/runtime file in release inventory: {relative}"
                )
            if item.is_symlink() or not item.resolve().is_relative_to(ROOT):
                raise ValueError(f"Release input escapes project: {relative}")
            archive.write(item, f"{prefix}/{relative.as_posix()}")


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    files = {ROOT / name for name in TOP_FILES}
    for pattern in PATTERNS:
        files.update(path for path in ROOT.glob(pattern) if path.is_file())
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise ValueError(f"Missing release inputs: {missing}")
    source = dist / f"argelius-doppler-lab-{__version__}-source.zip"
    write_zip(source, files, f"Argelius-Doppler-Lab-{__version__}")
    student_docs = {
        "STUDENT_LAB.md",
        "GUIDE.md",
        "METHOD.md",
        "DATA.md",
        "INVESTIGATION_WORKFLOW.md",
        "DATA_VOLUME.md",
        "BROAD_SEARCH.md",
        "BINARIES.md",
        "FIELD_PROTOCOL.md",
        "STUDENT_PACK.md",
    }
    student = {ROOT / "LICENSE"}
    student.update(
        path for path in files if path.parent == ROOT / "docs" and path.name in student_docs
    )
    student.update(path for path in files if "assets" in path.relative_to(ROOT).parts)
    student.update(
        path
        for path in files
        if path.is_relative_to(ROOT / "examples")
        and path.name not in {"truth.json", "benchmark.json", "README.md"}
    )
    pack = dist / f"argelius-doppler-lab-{__version__}-student-pack.zip"
    write_zip(pack, student, "Doppler-Lab-Student-Pack")
    with zipfile.ZipFile(pack, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(
            "Doppler-Lab-Student-Pack/README.md",
            (ROOT / "docs" / "STUDENT_PACK.md").read_text(encoding="utf-8"),
        )
    inventory = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in sorted(files)
    }
    (dist / "source-inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    artifacts = [source, pack, dist / "source-inventory.json"]
    artifacts.extend(sorted(dist.glob(f"argelius_doppler_lab-{__version__}-*.whl")))
    artifacts.extend(sorted(dist.glob(f"argelius_doppler_lab-{__version__}.tar.gz")))
    (dist / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in artifacts), encoding="utf-8"
    )
    for path in artifacts:
        print(f"{path.name}: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
