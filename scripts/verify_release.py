"""Check local documentation links, report assets, provenance and archive contents."""

import base64
import hashlib
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

from doppler_lab import __version__

ROOT = Path(__file__).resolve().parents[1]


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = 0
        self.headings = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"script", "iframe", "object"}:
            raise ValueError(f"Unexpected active report element: {tag}")
        if tag == "link" and attributes.get("href", "").startswith(("http:", "https:")):
            raise ValueError("Report depends on an external stylesheet or asset.")
        if tag == "img":
            assert attributes.get("alt"), "Missing alternative text"
            uri = attributes["src"]
            assert uri.startswith("data:image/png;base64,"), "Report image is not self-contained"
            data = base64.b64decode(uri.split(",", 1)[1], validate=True)
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            self.images += 1
        if tag in {"h1", "h2"}:
            self.headings.append(tag)


def main():
    files = [*ROOT.glob("*.md"), *ROOT.glob("docs/*.md"), *ROOT.glob("examples/*.md")]
    for file in files:
        text = file.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if target.startswith(("https:", "http:", "#")):
                continue
            target = target.split("#", 1)[0]
            assert (file.parent / target).exists(), f"Broken link in {file.name}: {target}"
    parser = ReportParser()
    parser.feed((ROOT / "examples/report/report.html").read_text(encoding="utf-8"))
    assert parser.images == 2 and parser.headings.count("h1") == 1
    result = json.loads((ROOT / "examples/report/results.json").read_text(encoding="utf-8"))
    assert result["accepted_location"] is False
    assert result["candidate_count"] == len(result["rows"]) == 289
    for key, filename in [
        ("case", "case.json"),
        ("audio", "recording.wav"),
        ("tracks", "tracks.csv"),
    ]:
        digest = hashlib.sha256((ROOT / "examples/classroom" / filename).read_bytes()).hexdigest()
        assert digest == result["input_sha256"][key], f"Sample provenance mismatch: {filename}"
    archives = list((ROOT / "dist").glob(f"argelius-doppler-lab-{__version__}-*.zip"))
    assert len(archives) == 2, "Expected source and student ZIPs"
    for path in archives:
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                assert not any(
                    part in {"work", "local-review", ".venv", ".tmp", "__pycache__"}
                    for part in Path(name).parts
                ), name
                assert not name.endswith((".webm", ".srt", ".pyc")), name
                if "student-pack" in path.name:
                    assert not name.endswith(("truth.json", "INSTRUCTOR_GUIDE.md")), name
            assert any(name.endswith("LICENSE") for name in archive.namelist())
    print(
        f"Verified {len(files)} Markdown files, self-contained report images, input hashes, "
        f"and {len(archives)} clean archives."
    )


if __name__ == "__main__":
    main()
