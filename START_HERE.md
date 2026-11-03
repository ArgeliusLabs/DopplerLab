# Argelius Doppler Lab — start here

This folder contains the experimental aircraft-audio investigation toolkit prepared for
Argelius Labs, with a classroom lab inspired by colsto's aircraft Doppler video.

| Start with | What you get |
| --- | --- |
| [README](README.md) | Installation, CLI and project scope |
| [Investigation workflow](docs/INVESTIGATION_WORKFLOW.md) | How a broad region and recording date lead to candidate areas and local matching |
| [Download and storage guide](docs/DATA_VOLUME.md) | Verified daily archive sizes, transfer estimates and working-space planning |
| [Real-data benchmark](docs/REAL_DATA_BENCHMARK.md) | Measured U.S., European and Tucson processing times, retained storage and limitations |
| [Broad-search commands](docs/BROAD_SEARCH.md) | Download, regional index, timing shortlist and local handoff |
| [Native binaries](docs/BINARIES.md) | Windows, Linux and macOS build candidates and release packaging |
| [Example report](examples/report/report.html) | A complete offline result; open in a browser |
| [Research review](docs/RESEARCH.md) | Video analysis, sources, physical limits and related work |
| [Public guide](docs/GUIDE.md) | A practical walkthrough from sound to a testable hypothesis |
| [Student lab](docs/STUDENT_LAB.md) | A 110-minute intermediate OSINT exercise |
| [Instructor guide](docs/INSTRUCTOR_GUIDE.md) | Schedule, answer key, rubric and troubleshooting |
| [Validation record](docs/VALIDATION.md) | Measured results and what remains unproven |
| [Release plan](docs/RELEASE_PLAN.md) | Packaging, demonstration script and classroom pilots |
| [Community roadmap](docs/ROADMAP.md) | Open research priorities and ways to contribute |

In the prepared workspace, source and student archives are in `dist/`, with checksums.
If you are reading an extracted source ZIP, this folder is already the source release.
The sample data are fictional. The third-party video and transcript are not bundled.
Project home: [ArgeliusLabs/DopplerLab](https://github.com/ArgeliusLabs/DopplerLab).
Download packaged artifacts from [Releases](https://github.com/ArgeliusLabs/DopplerLab/releases).

The key result is reproducibility: the two-event synthetic example recovers the correct
aircraft pair, while controls expose how a wrong model or missing aircraft can mislead.
It is not a claim of proven real-world location accuracy.
