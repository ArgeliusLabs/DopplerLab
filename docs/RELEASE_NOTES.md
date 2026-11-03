# Development candidate: 0.2.0.dev1

The development branch adds daily adsb.lol archive downloads, streaming regional
indexes, two-flyover timing shortlists and a local track handoff. Every stage records
source hashes, assumptions, work limits and completion state. Candidate areas still
require analyst-reviewed audio and detailed local matching.

Windows x86-64, Linux x86-64, Intel Mac and Apple Silicon binaries are built and smoke
tested on their respective GitHub runners. Successful workflow runs provide temporary
build artifacts. A future manual release can attach all four native archives, license
notices and checksums alongside the source/student packages.

The local regression suite contains 38 tests. The downloaded November 2 global
archive is 3.502 GB and took 4 minutes 52 seconds on the development connection. Regional
indexing and screening are benchmarked separately. This is not field-accuracy evidence.

**No new release is authorized until two original recording cases have been validated.**
Those recordings are not yet available. Development pushes no longer publish releases
automatically, and the manual publishing job rejects `.dev` versions. The existing
v0.1.0 assets remain available. See [broad-search instructions](BROAD_SEARCH.md),
[native builds](BINARIES.md) and [validation](VALIDATION.md).

## Historical notes: v0.1.0

The first experimental community release: an offline aircraft Doppler matching
toolkit and a 110-minute lab for intermediate OSINT students, inspired by
[colsto's demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI).

## Start here

- Download the **source ZIP** for the toolkit, installation guide, original fixtures,
  research review, tests, student handout and instructor guide.
- Download the **student-pack ZIP** for an interpretation exercise with an existing
  report. This pack omits the instructor answer key and truth file; the full public
  source deliberately includes both.
- The **Python wheel** provides the command-line tool. Documentation and classroom
  fixtures are in the source ZIP.
- `SHA256SUMS.txt` records artifact hashes; `source-inventory.json` records the source
  file hashes in this release.

## Included

Generate fictional audio and candidate trajectories, inspect spectrograms, account
for sound travel time, fit a common recording clock across flyovers, and compare
candidate receiver positions. Reports include score maps, predicted curves, full
candidate tables and input hashes.

The classroom materials teach data preparation, ambiguity, negative controls and
defensible reporting. The field protocol describes the next validation step.

## Validation and limits

Publication is gated by the 26-test suite, lint/format checks, package builds, archive
verification and the command-line demo on Windows and Linux with Python 3.11 and 3.13.
See the [validation record](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.1.0/docs/VALIDATION.md)
for the ten-condition synthetic benchmark.

This is **synthetically validated teaching software**. No real-world location accuracy
or false-localization rate has been established. Scores are not probabilities, and
the tool never marks a location as accepted. A missing aircraft or an incorrect sound
speed can produce a convincing wrong result.

## Help improve it

Try the quickstart or teach the lab; report confusing steps and reproducible failures.
See the [roadmap](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.1.0/docs/ROADMAP.md)
and [contribution guide](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.1.0/CONTRIBUTING.md).
Questions, corrections and unsuccessful experiments are welcome in
[Issues](https://github.com/ArgeliusLabs/DopplerLab/issues).

Original code, documentation and fictional fixtures are MIT licensed. The source
video and third-party flight databases are not bundled. Related work is credited in
the README and research review.
