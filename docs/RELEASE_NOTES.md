# v0.2.0 — experimental investigation toolkit

**Testing in progress.** Automated tests, native executable smoke checks and full-day
archive/search benchmarks have passed. Original-recording field tests are still being
prepared; real-world location accuracy and false-localization rates are unvalidated.
This is an experimental community release, not a validated location-identification service.

## New in this release

- Download and hash daily adsb.lol archives; stream compressed traces into regional indexes.
- Screen two-flyover timing hypotheses across broad regions, then reuse indexes for smaller areas.
- Filter candidates with separate speed/slant bounds for each event and export tracks for local matching.
- Run the bundled command-line tool without installing Python on four supported platforms.
- Inspect measured U.S., European and Tucson processing times, storage, counts and source provenance.
- Use the existing fictional audio lab, reports, student pack and instructor materials for teaching.

Audio-event selection, supported search bounds, terrain/height choices and interpretation
still require investigator review. Candidate rows are alternatives, not confidence scores;
the software never marks a location as accepted.

## Native downloads

- [Windows x86-64 ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.0/doppler-lab-0.2.0-windows-x86_64.zip)
- [Linux x86-64 archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.0/doppler-lab-0.2.0-linux-x86_64.tar.gz)
- [Intel Mac archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.0/doppler-lab-0.2.0-macos-x86_64.tar.gz)
- [Apple Silicon archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.2.0/doppler-lab-0.2.0-macos-arm64.tar.gz)

Extract the archive and run the executable from a terminal. These are command-line
applications. Python dependencies and third-party license notices are bundled; FFmpeg
is optional and separate. Builds are unsigned and not notarized. See the
[native guide](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.0/docs/BINARIES.md)
for tested OS versions, startup commands and checksum verification.

The release also includes the complete source ZIP, portable student pack, Python wheel,
source distribution, source inventory and `SHA256SUMS.txt`. The MIT code license permits
reuse, including commercial use; third-party aircraft data retain their own terms.

## What has been checked

The 39-test suite runs on Windows and Linux with Python 3.11 and 3.13. Each native build
is exercised on its target OS outside the source checkout, including archive indexing,
coarse screening, filtering, export, fictional audio matching and report generation.

The November 2 global archive downloaded as 3.502 GB in 4 minutes 52 seconds on the
development connection. After indexing, the deliberately broad timing screen took
46 minutes 46 seconds for the U.S. rectangle and 23 minutes 47 seconds for Europe.
These runs used a hypothetical interval and flat receiver height, leaving millions of
alternatives. They measure processing feasibility, not audio-location accuracy.

See the [full benchmark](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.0/docs/REAL_DATA_BENCHMARK.md)
and [validation record](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.0/docs/VALIDATION.md).
The first two original-recording cases remain planned. Publication is proceeding with
that testing status disclosed; community experiments and corrections are welcome.

## Start and contribute

Follow the [investigation workflow](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.0/docs/INVESTIGATION_WORKFLOW.md)
and [broad-search commands](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.2.0/docs/BROAD_SEARCH.md).
Report reproducible successes and failures through
[GitHub Issues](https://github.com/ArgeliusLabs/DopplerLab/issues).

Inspired by [colsto's aircraft Doppler demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI).
Original implementation by Argelius Labs; no affiliation is implied. The source video
and third-party flight archives are not bundled. The prior
[v0.1.0 release](https://github.com/ArgeliusLabs/DopplerLab/releases/tag/v0.1.0) remains available.
