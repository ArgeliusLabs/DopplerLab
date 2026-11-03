# Aircraft data: download time and storage

Checked **3 November 2026**. The byte counts below come from GitHub release-asset
metadata for two complete UTC days. We subsequently downloaded the complete November 2
archive: **3,501,931,008 bytes in 291.507 seconds (4 minutes 52 seconds)**, including
writing and hashing the files. We also measured regional indexing and timing screens;
see the [real-data benchmark](REAL_DATA_BENCHMARK.md) for complete results and settings.
The bandwidth table remains a calculation; workspace reservations are planning
estimates. Acquisition and screening timings are not geolocation accuracy measurements.

## A concrete open-data example

The [adsb.lol historical archive](https://www.adsb.lol/docs/open-data/historical)
provides daily dumps of its observed worldwide coverage. The current repository
resolved to [adsblol/globe_history_2026](https://github.com/adsblol/globe_history_2026).
Each selected release is an instance/day; the assets are parts of a tar containing
gzip-compressed JSON records. The underlying schema is documented by
[readsb](https://github.com/wiedehopf/readsb/blob/dev/README-json.md#trace-jsons).

| UTC date, instance | Part `.aa` | Part `.ab` | Total download | Binary units |
| --- | ---: | ---: | ---: | ---: |
| [2026-11-01, prod-0](https://github.com/adsblol/globe_history_2026/releases/tag/v2026.11.01-planes-readsb-prod-0) | 2,000,000,000 bytes | 1,118,588,416 bytes | **3.119 GB** | 2.904 GiB |
| [2026-11-02, prod-0](https://github.com/adsblol/globe_history_2026/releases/tag/v2026.11.02-planes-readsb-prod-0) | 2,000,000,000 bytes | 1,501,931,008 bytes | **3.502 GB** | 3.261 GiB |

GB means 1,000,000,000 bytes; GiB means 1,073,741,824 bytes. These are two observed
examples, not a guaranteed daily upper bound or a long-term average. Archive size
changes with traffic, reception, retention settings and outages.

**For either the contiguous U.S. or Europe, this acquisition route starts with the
same roughly 3.1–3.5 GB worldwide day.** Filter to the intended region after download.
The measured normalized indexes were **0.930 GB for the U.S. rectangle** and
**0.463 GB for the European rectangle** after source, height and quality filtering.
These are compressed indexes of usable trajectory segments, not every regional flight.
Do not estimate regional bytes from land area or promise that one network captures
every flight. Coverage, low-altitude reception and available geometric heights vary.

Do not add production, staging and MLAT-only release sizes together as though all were
mandatory geographic pieces. Start with one suitable production release and assess
its completeness; another instance is a fallback or a separately evaluated supplement.

## How long is the transfer?

Using the two totals above:

| Sustained transfer rate | Calculated transfer time for one day |
| --- | ---: |
| 25 Mbps | 16 minutes 38 seconds – 18 minutes 41 seconds |
| 100 Mbps | 4 minutes 10 seconds – 4 minutes 40 seconds |
| 500 Mbps | 50–56 seconds |

Calculation: `seconds = bytes * 8 / (megabits_per_second * 1_000_000)`.
Mbps is megabits per second, not megabytes per second. At a sustained 100 Mbps,
the payload rate is 12.5 MB/s. These estimates exclude connection setup, protocol
overhead, retries and disk work; the advertised speed of an internet plan is not
necessarily the sustained download rate from GitHub. Provider/CDN limits can dominate.

Our measured transfer averaged about **96.1 Mbps**. That is one observation on one
connection and provider route, not a speed guarantee. A few minutes is plausible. It does
not establish a few-minute end-to-end geolocation search. A per-flight historical API
can take much longer than a bulk archive because of request count, pagination, credits
and rate limits, even when its final dataset is smaller. The video's reported several
hours of acquisition is not a benchmark for these bulk releases.
This is also a different provider and dataset from the video's acquisition. Smaller
downloads do not establish equivalent reception coverage, sampling density or matching
accuracy.

## Disk space and memory

For the larger, 3.502 GB example:

| Retained material | Approximate disk requirement |
| --- | ---: |
| Original downloaded parts only | **3.5 GB** |
| Parts plus extracted, still-gzipped records | **About 7 GB**, plus filesystem overhead |
| Parts, an additional joined tar, and extracted gzipped records | **About 10.5 GB**, plus filesystem overhead |
| U.S. normalized index | **0.930 GB** additional |
| European normalized index | **0.463 GB** additional |
| U.S. coarse timing-screen output | **13.889 GB** additional |
| European coarse timing-screen output | **3.619 GB** additional |
| Fully expanded trace JSON payloads | **17.632 GB**, based on gzip footer sizes; not written |

Extracting the tar and decompressing every JSON record are different operations.
The tar already holds compressed records. Expanding all JSON at once or loading it
as Python objects can use much more disk or memory than the download size suggests.
Filesystem overhead can also matter when extracting many small files.

For a first one-day experiment, **reserve 20–50 GB of free workspace** as a practical
starting budget, not as a measured requirement or guaranteed ceiling. Preserve the
download, process compressed traces incrementally, filter early and retain only the
normalized data needed for the investigation. The development indexer reads split
archives and compressed records directly: it creates neither a joined tar nor an
extracted JSON tree. Broad searches can still produce multi-gigabyte candidate files.
See the benchmark's retained-storage totals; those exclude temporary files and failed
experiments. Measure peak disk and memory before setting hardware requirements.
Measured indexer process RAM peaked near **192 MB** in 0.2-second samples, on a machine
with about 64 GiB of RAM. That does not establish a minimum-memory requirement or account
for the operating system's filesystem cache. The detailed local solver remains a
separate bounded operation.

Audio, DEM tiles, multiple days, extra provider coverage and repeated output copies
consume additional space. Two adjacent global UTC days at the observed sizes would
require roughly 6.2–7.0 GB just for downloads.

## How to get the right archive

1. Establish the recording's supported UTC interval, including uncertainty and enough
   padding around events for flight motion and sound travel. A local calendar date is
   not necessarily one UTC day.
2. Open the provider's release list and find the relevant date and production instance.
   The repository name may change by year; follow the provider's historical-data page
   and verify the resolved repository. Inspect the asset sizes and compare neighboring
   days or another instance for obvious incompleteness.
3. Download **all archive parts for that one selected release**: `.aa`, `.ab`, and any
   later parts present. GitHub's automatically generated "Source code" ZIP and tar.gz
   are the repository source, not the aircraft dataset.
4. Preserve the original names, byte counts, download time, release URL and SHA-256
   hashes. Doppler Lab's indexer streams parts in suffix order without
   extraction. For independent manual processing, use binary-safe tools; the provider
   documents a `cat ... | tar ...` streaming example for Unix.
   Do not use PowerShell text concatenation (`Get-Content`/`Set-Content`) for these bytes.
5. Read the compressed trace records incrementally. Filter by the supported region
   and UTC interval, keeping boundary context, quality/source fields and compatible
   heights. Preserve the raw archive as evidence.
6. Build the broad candidate shortlist, then prepare local cases using
   [DATA.md](DATA.md). The [investigation workflow](INVESTIGATION_WORKFLOW.md) explains
   the method, and [BROAD_SEARCH.md](BROAD_SEARCH.md) provides the v0.2.0 commands.
   The older v0.1.0 CLI predates the archive and shortlist commands.

To independently recheck the published size without downloading the multi-gigabyte
assets, this PowerShell example reads only public release metadata:

```powershell
$releaseUrl = 'https://api.github.com/repos/adsblol/globe_history_2026/releases/tags/v2026.11.02-planes-readsb-prod-0'
$release = Invoke-RestMethod -Uri $releaseUrl
$parts = @($release.assets | Where-Object { $_.name -match '\.tar(\.[a-z]{2})?$' })
if ($parts.Count -eq 0) { throw 'No archive assets found; inspect the release.' }
$parts | Select-Object name, size, browser_download_url
$byteCount = ($parts | Measure-Object -Property size -Sum).Sum
[pscustomobject]@{
    Bytes = $byteCount
    GB = [math]::Round($byteCount / 1e9, 3)
    GiB = [math]::Round($byteCount / 1GB, 3)
    MinutesAt100Mbps = [math]::Round($byteCount * 8 / 100e6 / 60, 2)
}
```

Keep the data's ODbL attribution and applicable terms separate from this project's MIT
code license. See [data sources and licensing](DATA.md#data-sources-and-course-licensing).

## Tucson date example

Tucson's local **3 November 2026** runs from **2026-11-03 07:00 UTC** to
**2026-11-04 07:00 UTC**, using the exclusive end of the interval. Searching that entire
local day therefore touches two daily UTC archives, with extra boundary padding if
required. A short recording with a known UTC time can need a much smaller time slice,
but a bulk-only source still requires downloading the containing archive(s).
The current shortlist operates on one index and does not join event pairs across daily
indexes. A pair spanning midnight needs additional implementation; separate successful
day searches do not establish that the boundary was covered.

The current day is incomplete until it ends, and a daily archive is only available
after the provider publishes it. To test a new recording before publication, collect
live trajectories concurrently through an access route whose rate limits support the
sampling you need, or wait for the historical data. Missing samples and coarse archived
traces can prevent reliable local fitting even when downloading succeeds.

## Processing time after download

The [real-data benchmark](REAL_DATA_BENCHMARK.md) separates download, indexing, coarse
candidate generation and regional refinement. U.S. indexing took **16 min 14 s**,
followed by **46 min 46 s** for its coarse screen. European indexing took **13 minutes
7 seconds**, followed by **23 minutes 47 seconds** for the deliberately broad timing
screen. Starting from the existing U.S. index, a Tucson subset took **9.2 seconds** and
its finer timing screen **26.4 seconds**. Reuse an index when testing another region or
audio hypothesis; do not download and parse the global day again unnecessarily.

Those searches used a hypothetical interval and a flat receiver height, with millions
of broad alternatives. Audio interpretation, terrain, candidate comparison and detailed
matching add work. Their complete real-recording cost and accuracy remain unmeasured.
