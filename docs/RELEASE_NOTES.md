# v0.3.0 — terrain for real investigation workflows

**Experimental — testing in progress.** This release adds automatic USGS DEM acquisition
and applies terrain heights in both broad screening and detailed local preparation.
Real-recording location accuracy remains unvalidated; the owner's iPad recording has
not yet been supplied for analysis.

## New capabilities

- `download-terrain`: fetch current contiguous-US USGS 3DEP 1/3 arc-second tiles and
  the correction grids required by an explicit NAD83/NAVD88 to WGS84 height operation.
- `terrain-point`: inspect a verified local bundle's receiver height offline.
- `prepare-observers`: create terrain-following local candidates, geographic coordinates,
  an explicit origin and provenance for detailed Doppler matching.
- `shortlist --terrain`: use each candidate's actual ground-derived height. Exported
  candidates preserve those heights and terrain provenance.
- Microphone height and height-sensitivity offsets, bounded streaming downloads,
  SHA-256 checks, and explicit errors for missing terrain or correction grids.

These commands are included in the Windows, Linux and Mac executables. No separate
Python/GIS installation is needed for terrain operations in the native builds. DEMs
are downloaded for the chosen region and reused offline; they are not bundled globally.

## Start here

- [Native quick start](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.3.0/QUICKSTART.md)
- [Step-by-step terrain guide](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.3.0/docs/TERRAIN.md)
- [Investigation workflow](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.3.0/docs/INVESTIGATION_WORKFLOW.md)
- [Recorded Tucson terrain checks](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.3.0/examples/terrain-benchmark.json)

Quick start, guided practice, platform instructions and the terrain guide ship inside
each native archive. Video extraction still uses a separately installed FFmpeg.

## Evidence so far

The Tucson download retained two real DEM tiles plus correction grids/notices:
**828,398,104 bytes in 137.089 seconds**. Three same-reference terrain samples differed
from the independent USGS point service by 0.002, 1.813 and 1.606 metres; the service
used finer source data. Those are consistency checks, not survey accuracy estimates.

A real Tucson aircraft index was screened using 1,707 terrain nodes with heights from
614.932 to 2,729.908 metres. The 920-second interval was hypothetical. A separate local
preparation produced 12,882 terrain-following candidates. Neither used the owner's video.

All 51 regression tests pass locally. Publication requires the Windows/Linux test matrix
and native executable checks on Windows, Linux, Intel Mac and Apple Silicon. The actual
Windows executable also reproduced the source implementation's height on the real Tucson DEM.

## Downloads

- [Windows x86-64 ZIP](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.3.0/doppler-lab-0.3.0-windows-x86_64.zip)
- [Linux x86-64 archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.3.0/doppler-lab-0.3.0-linux-x86_64.tar.gz)
- [Intel Mac archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.3.0/doppler-lab-0.3.0-macos-x86_64.tar.gz)
- [Apple Silicon archive](https://github.com/ArgeliusLabs/DopplerLab/releases/download/v0.3.0/doppler-lab-0.3.0-macos-arm64.tar.gz)

Source ZIP, student pack, Python wheel, source distribution, inventory and SHA-256 checksums
are also included. Read [platform requirements](https://github.com/ArgeliusLabs/DopplerLab/blob/v0.3.0/docs/BINARIES.md).

## Limits and community work

Automatic terrain support currently covers bounded contiguous-US regions, up to 32 tiles
per download and one supported coordinate operation per region. Other terrain providers
and arbitrary GeoTIFF import are not implemented. Coarse grid sampling does not prove
search completeness in steep terrain. The DEM does not model acoustic blockage,
reflections, buildings, wind or refraction. See the terrain guide for uncertainty and
height-sensitivity instructions.

Original implementation by Argelius Labs, inspired by
[colsto's aircraft Doppler demonstration](https://www.youtube.com/watch?v=UytYrhYLOKI).
No affiliation or endorsement is implied. Share reproducible successes and failures in
[Issues](https://github.com/ArgeliusLabs/DopplerLab/issues); avoid posting private recordings
or precise recording locations without permission.
