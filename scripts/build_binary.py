"""Build on the target OS; bundle notices, hash the archive, and record the environment."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import ssl
import subprocess
import sys
import sysconfig
import urllib.request
from pathlib import Path

import certifi

from doppler_lab import __version__

ROOT = Path(__file__).resolve().parents[1]


def platform_tag():
    system = {"Windows": "windows", "Linux": "linux", "Darwin": "macos"}[platform.system()]
    machine = platform.machine().lower()
    arch = {"amd64": "x86_64", "x86_64": "x86_64", "aarch64": "arm64", "arm64": "arm64"}.get(
        machine
    )
    if arch is None:
        raise ValueError(f"Unsupported native architecture: {machine}")
    return f"{system}-{arch}"


def notices(destination):
    license_dir = destination / "THIRD_PARTY_LICENSES"
    license_dir.mkdir()
    packages = []
    for dist in sorted(
        importlib.metadata.distributions(), key=lambda d: d.metadata["Name"].lower()
    ):
        name = dist.metadata["Name"]
        packages.append(
            {
                "name": name,
                "version": dist.version,
                "license": dist.metadata.get("License-Expression")
                or dist.metadata.get("License", "See bundled license files"),
            }
        )
        for item in dist.files or []:
            if not any(word in item.name.lower() for word in ("license", "copying", "notice")):
                continue
            source = Path(dist.locate_file(item))
            if not source.is_file() or source.stat().st_size > 2_000_000:
                continue
            package = license_dir / re.sub(r"[^A-Za-z0-9._-]", "_", name)
            package.mkdir(exist_ok=True)
            relative = re.sub(r"[^A-Za-z0-9._-]", "_", str(item))
            shutil.copyfile(source, package / relative)
    candidates = [
        Path(sys.base_prefix) / "LICENSE.txt",
        Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
    ]
    python_license = next((p.read_bytes() for p in candidates if p.is_file()), None)
    if python_license is None:
        url = (
            f"https://raw.githubusercontent.com/python/cpython/v{platform.python_version()}/LICENSE"
        )
        with urllib.request.urlopen(
            url, timeout=30, context=ssl.create_default_context(cafile=certifi.where())
        ) as response:
            python_license = response.read()
    (license_dir / "CPython-LICENSE.txt").write_bytes(python_license)
    (destination / "BUILD_INFO.json").write_text(
        json.dumps(
            {
                "tool_version": __version__,
                "platform": platform.platform(),
                "python": platform.python_version(),
                "architecture": platform.machine(),
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "git_worktree_dirty": bool(
                    subprocess.check_output(
                        ["git", "status", "--porcelain"], cwd=ROOT, text=True
                    ).strip()
                ),
                "source_sha256": {
                    str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
                        p.read_bytes()
                    ).hexdigest()
                    for p in sorted(
                        [
                            *ROOT.glob("src/**/*.py"),
                            ROOT / "pyproject.toml",
                            ROOT / "scripts/build_binary.py",
                            ROOT / "scripts/smoke_binary.py",
                        ]
                    )
                },
                "packages": packages,
                "notes": "Build environment inventory may include test/build tools not embedded in the executable. Dependencies retain their own licenses. This build is not publisher-signed or notarized.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "native")
    parser.add_argument("--work", type=Path, default=ROOT / "build" / "native")
    args = parser.parse_args()
    if args.target != platform_tag():
        raise ValueError(
            f"Build on the intended architecture: running {platform_tag()}, requested {args.target}."
        )
    output, work = args.output.resolve(), args.work.resolve()
    if output.exists() or work.exists():
        raise ValueError("Choose new build/output directories to preserve previous candidates.")
    output.mkdir(parents=True)
    work.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            "doppler-lab",
            "--distpath",
            str(work / "app"),
            "--workpath",
            str(work / "build"),
            "--specpath",
            str(work),
            "--paths",
            str(ROOT / "src"),
            "--exclude-module",
            "tkinter",
            "--exclude-module",
            "IPython",
            "--exclude-module",
            "pytest",
            "--hidden-import",
            "ijson.backends.yajl2_c",
            "--hidden-import",
            "ijson.backends.python",
            str(ROOT / "scripts" / "frozen_entry.py"),
        ],
        check=True,
        cwd=ROOT,
    )
    bundle = output / f"doppler-lab-{__version__}-{args.target}"
    bundle.mkdir()
    executable = "doppler-lab.exe" if platform.system() == "Windows" else "doppler-lab"
    shutil.copy2(work / "app" / executable, bundle / executable)
    shutil.copyfile(ROOT / "LICENSE", bundle / "LICENSE")
    shutil.copyfile(ROOT / "docs" / "BINARIES.md", bundle / "README.md")
    notices(bundle)
    archive_format = "zip" if platform.system() == "Windows" else "gztar"
    archive = Path(
        shutil.make_archive(str(bundle), archive_format, root_dir=output, base_dir=bundle.name)
    )
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"executable": str(bundle / executable), "archive": str(archive), "sha256": digest}
        )
    )


if __name__ == "__main__":
    main()
