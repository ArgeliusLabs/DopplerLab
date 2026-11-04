# v0.2.2 — built for investigations

**Experimental — testing in progress.** Argelius Doppler Lab is an aircraft-audio
investigation toolkit for OSINT practitioners. Real-recording location accuracy remains
unvalidated; the existing automated checks and archive-processing benchmarks are documented.

## Branding corrections

The banner now reads **OPEN SOURCE · BUILT FOR INVESTIGATIONS**. The README and start
page lead with acquiring aircraft trajectories, screening candidate areas, comparing
Doppler curves and preserving evidence. Reports use neutral implementation attribution.

Guided practice and classroom materials remain optional resources for learning and
teaching the investigation workflow. They do not define the tool's primary purpose.
The analysis algorithms and candidate-scoring behavior are unchanged.

## Get started

- [Native quick start](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.2/QUICKSTART.md)
- [Investigation workflow](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.2/docs/INVESTIGATION_WORKFLOW.md)
- [Guided practice](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.2/docs/PRACTICE.md)

The quick start and practice guides remain bundled in every native archive.

## Downloads

- [Windows x86-64 ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-windows-x86_64.zip)
- [Linux x86-64 archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-linux-x86_64.tar.gz)
- [Intel Mac archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-macos-x86_64.tar.gz)
- [Apple Silicon archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.2/doppler-lab-0.2.2-macos-arm64.tar.gz)

The source ZIP, student pack, Python wheel, source distribution, inventory and checksums
are also included. Native packages contain build provenance and dependency notices.
See [platform requirements](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.2/docs/BINARIES.md).

Publication requires all 39 regression tests across the Windows/Linux matrix, package
checks and native executable checks on all four supported platforms. The corrected
SVG was rendered and visually checked; the static example report's input hashes remain
unchanged. Existing versioned releases remain available.

Original implementation by Argelius Labs, inspired by
[colsto's aircraft Doppler demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI).
No affiliation or endorsement is implied. Community investigation feedback is welcome
in [Issues](https://github.com/ArgeliusLabs/DopplerLab/issues).
