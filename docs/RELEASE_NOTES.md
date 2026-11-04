# v0.2.1 — native quick start and guided practice

**Experimental — testing in progress.** Automated checks and archived-flight processing
benchmarks are complete; original-recording location accuracy remains unvalidated.

## Start here

- [Five-minute quick start](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.1/QUICKSTART.md): choose a binary, extract it, open a terminal, generate a fictional case and view the report.
- [15–20 minute guided practice](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.1/docs/PRACTICE.md): inspect both flyovers, compare candidate locations, run a noise-only control and check your assessment.

Both work without installing Python, buying flight data or supplying a recording. The
executable generates the fictional audio and tracks locally; the practice runs offline.

## What changed

Every native archive now opens with a quick-start `README.md` and also contains
`QUICKSTART.md`, `docs/PRACTICE.md` and `docs/BINARIES.md`. The instructions stay with the
download. Source and student packages include the same guides.

The repository home page now starts with native downloads and the guided practice.
The full 110-minute lab's core steps use the native executable and a text editor;
Python is only needed for optional source helpers and benchmark scripts. The short
practice contains a clearly marked self-check for the default fictional fixture.

This is a documentation and packaging update. The Doppler model, archive-processing
logic and candidate-scoring behavior are unchanged from v0.2.0. Existing v0.2.0 binaries
can follow the new walkthrough too.

## Native downloads

- [Windows x86-64 ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.1/doppler-lab-0.2.1-windows-x86_64.zip)
- [Linux x86-64 archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.1/doppler-lab-0.2.1-linux-x86_64.tar.gz)
- [Intel Mac archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.1/doppler-lab-0.2.1-macos-x86_64.tar.gz)
- [Apple Silicon archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.1/doppler-lab-0.2.1-macos-arm64.tar.gz)

Also included: source ZIP, student pack, Python wheel, source distribution, source
inventory and `SHA256SUMS.txt`. Native packages contain dependency license notices and
build provenance. Builds are unsigned and not notarized; see the
[native guide](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.1/docs/BINARIES.md)
for tested platforms and requirements. Video extraction needs separate FFmpeg; the
fictional practice does not.

## Validation and next steps

Publication requires the 39-test Windows/Linux matrix, source/student package checks,
and native executable smoke checks on Windows, Linux, Intel Mac and Apple Silicon.
The guides distinguish a ranked hypothesis from an accepted location, including the
noise-only example where the search still has a winner.

See the [real-data benchmark](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.1/docs/REAL_DATA_BENCHMARK.md)
and [validation record](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.1/docs/VALIDATION.md)
for completed checks and remaining field work. Reproducible community feedback is welcome
in [Issues](https://github.com/ArgeliusLabs/DopplerLab/issues).

Inspired by [colsto's aircraft Doppler demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI).
Original implementation by Argelius Labs; no affiliation is implied. Code and generated
fixtures are MIT-licensed; third-party data retain their own terms. The previous
[v0.2.0 release](https://github.com/ArgeliusLabs/DopplerLab/releases/tag/v0.2.0) remains available.
