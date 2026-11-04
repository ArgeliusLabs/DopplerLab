# Argelius Doppler Lab — start here

This folder contains Argelius Labs' experimental aircraft-audio investigation toolkit
for OSINT practitioners, inspired by colsto's aircraft Doppler video. Optional practice
and teaching materials accompany the investigation workflow.

For real US recordings, use [terrain preparation](docs/TERRAIN.md) to download and apply
DEM heights in both broad screening and local matching.

| Start with | What you get |
| --- | --- |
| [Native quick start](QUICKSTART.md) | Choose a binary, generate fictional audio and open a report without installing Python |
| [Guided practice](docs/PRACTICE.md) | A 15–20 minute walkthrough, noise-only comparison and self-check |
| [Original-recording walkthrough](docs/REAL_RECORDING.md) | Review a long video, acquire a local historical window, prepare terrain and test the hypothesis |
| [First field-test outcome](docs/FIELD_TEST_2026_11.md) | Real recording and flight data; insufficient acoustic evidence, with controls and limitations |
| [README](README.md) | Installation, CLI and project scope |
| [Investigation workflow](docs/INVESTIGATION_WORKFLOW.md) | How a broad region and recording date lead to candidate areas and local matching |
| [Download and storage guide](docs/DATA_VOLUME.md) | Verified daily archive sizes, transfer estimates and working-space planning |
| [Real-data benchmark](docs/REAL_DATA_BENCHMARK.md) | Measured U.S., European and Tucson processing times, retained storage and limitations |
| [Broad-search commands](docs/BROAD_SEARCH.md) | Download, regional index, timing shortlist and local handoff |
| [Native binaries](docs/BINARIES.md) | Windows, Linux and macOS downloads, platform requirements and checksums |
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
