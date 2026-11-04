# Native downloads

New here? Follow [Quick start](../QUICKSTART.md), then the
[guided practice](PRACTICE.md). Both guides ship inside each v0.2.2 native archive;
open its `README.md` or `QUICKSTART.md` first.

The [experimental v0.2.2 release](https://github.com/ArgeliusLabs/DopplerLab/releases/tag/v0.2.2)
includes standalone command-line executables for Windows x86-64, Linux x86-64,
macOS Intel and macOS Apple Silicon. Python and the runtime dependencies are bundled.
**Testing is in progress:** automated and native smoke checks have passed; original
recording tests are still being prepared. Real-world location accuracy is unvalidated.

Development candidates appear as `native-*` artifacts on successful runs of
[GitHub Actions](https://github.com/ArgeliusLabs/DopplerLab/actions). GitHub may require
sign-in to download workflow artifacts; they expire after 30 days. They are not a
published release. Use the versioned release assets above for persistent public downloads,
including source distributions, dependency notices and checksums.

The earlier v0.2.1 release passed all four native build/smoke jobs in
[this verified run](https://github.com/ArgeliusLabs/DopplerLab/actions/runs/41746624938).
Every published patch release must pass those jobs again. Inspect the conclusion and
source commit when selecting development artifacts.

## Choose a build

| v0.2.2 download | Target |
| --- | --- |
| [Windows ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-windows-x86_64.zip) | 64-bit Intel/AMD Windows; tested on Windows Server 2022 |
| [Linux archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-linux-x86_64.tar.gz) | Intel/AMD Linux with glibc 2.35 or newer; built on Ubuntu 22.04 |
| [Intel Mac archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-macos-x86_64.tar.gz) | Intel Mac; built and tested on macOS 15 |
| [Apple Silicon archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-macos-arm64.tar.gz) | Apple Silicon Mac; built and tested on macOS 15 |

Older macOS versions, Windows ARM and Linux ARM are not currently tested. Builds run
on each target OS; PyInstaller is not a cross-compiler. These candidates are unsigned
and not notarized, so operating-system trust controls may prevent execution. We do not
recommend disabling those controls. The Python installation route remains available.

Extract the archive, keep its license files and open a terminal in the extracted folder.
On Windows use `.\doppler-lab.exe`; on macOS/Linux use `./doppler-lab`:

```powershell
.\doppler-lab.exe --version
.\doppler-lab.exe --help
.\doppler-lab.exe demo --output my-case
.\doppler-lab.exe run my-case/case.json --output my-report
```

Open `my-report/report.html` in your browser. Use new output directories for each run.
The executable is a CLI, not a graphical application; double-clicking it may briefly
open and close a terminal. A one-file executable unpacks its bundled runtime into a
temporary directory when starting, which takes additional time and disk space.

The demo and local matching run offline. Archive acquisition and live capture require
internet access. FFmpeg remains a separate optional dependency for non-WAV extraction;
it is not bundled. Use the main repository's acquisition and broad-search guide for
the `download-day`, `index-archive`, `subset-index`, `shortlist`, `filter-candidates`
and `export-candidate` commands.

## Verify and reproduce

Development archives have SHA-256 sidecars. Release archives are listed in `SHA256SUMS.txt`.
Compare the downloaded file's hash before extracting:

```powershell
Get-FileHash .\doppler-lab-VERSION-windows-x86_64.zip -Algorithm SHA256
```

On Linux use `sha256sum`; on macOS use `shasum -a 256`. Hashes detect changed files;
they are not publisher signatures. `BUILD_INFO.json` records version, source commit,
OS, architecture, Python and installed packages. Its package inventory can include
build tools that are not embedded in the executable. Dependency licenses are included
under `THIRD_PARTY_LICENSES`; this project's MIT license does not replace them.

From a checkout on the matching platform:

```text
python -m pip install -e ".[dev,binary]"
python scripts/build_binary.py --target YOUR-PLATFORM
python scripts/smoke_binary.py PATH-TO-BUNDLED-EXECUTABLE
```

Build directories must be new. CI runs the executable from outside the checkout with
`PYTHONPATH` removed, exercises the synthetic audio workflow, and checks the broad-search
commands. CI success is packaging evidence, not validation of real-world geolocation.

References: [PyInstaller operating-system requirements](https://pyinstaller.org/en/stable/requirements.html),
[PyInstaller licensing exception](https://pyinstaller.org/en/stable/license.html).
