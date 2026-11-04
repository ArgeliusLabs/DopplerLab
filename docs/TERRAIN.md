# Terrain for aircraft-audio investigations

Available in **v0.3.0** and later, including the native executables. Terrain download,
height conversion and receiver preparation are implemented. Real-recording location
accuracy is still being tested. A DEM does not turn a ranked candidate into a verified location.

Aircraft altitude and ground elevation must describe compatible physical heights. A
DEM provides the ground elevation at each possible recording location; add the
microphone's height above that ground. These heights change slant range, predicted
Doppler and sound-arrival time. The fictional practice can remain flat.

## What this version supports

- Automatic retrieval of the current USGS 3DEP 1/3 arc-second DEM tiles for a bounded
  **contiguous-US** area. The approximately 10-metre spacing is not location accuracy.
- Explicit NAD83/NAVD88 to WGS84 ellipsoid conversion using a PROJ coordinate operation
  and its downloaded correction grids. No silent ballpark or zero-height fallback.
- Offline bilinear terrain sampling for the broad `shortlist` and local `prepare-observers`.
- A source manifest with query, URLs, publication dates, byte counts, SHA-256 hashes,
  raster references, conversion operation, library versions and correction-grid notices.
- Height sensitivity through `--height-offset`; microphone height through
  `--microphone-height` (default **1.5 metres above bare ground**).

Automatic non-US terrain providers and arbitrary GeoTIFF import are not implemented.
Do not rename an unrelated raster to make it look like a supported USGS product.

## 1. Download terrain for the search area

Use the executable from [Quick start](../QUICKSTART.md). Commands below use the installed
CLI spelling `doppler-lab`. In PowerShell substitute `.\doppler-lab.exe`; on Mac/Linux
use `./doppler-lab` when the executable is in the current directory.

Bounds always mean **south west north east**, in degrees. This example covers Tucson
and the Sabino Canyon area; it is a regional example, not a known recorder location.

```text
doppler-lab download-terrain --bounds 32.10 -111.15 32.55 -110.55 --max-gb 2 --output work/tucson-terrain
```

Internet access is needed for this command. No account or API key is required. The
byte budget includes the DEMs and correction grids; it is enforced while streaming.
The output directory must be new. Failed files retain `.partial` and the manifest is
marked failed; use a fresh directory after addressing the error. Resume is not implemented.

In our November 3, 2026 Arizona-time check, this downloaded two current DEM tiles plus
correction grids/notices: **828,398,104 bytes in 137.089 seconds**. Tile versions, speeds
and sizes will change. Whole one-degree source tiles are retained, so a small search
box can require a much larger raster download. Do not download a continent at 10 metres
as the first step; prepare bounded regions and reuse them.

Keep the entire folder, including `terrain.json`, `usgs-query.json`, TIFFs and `grids/`.
Reuse it for subsequent runs. All following commands read local files, verify their
hashes, and require no elevation-service calls.

## 2. Check a terrain point

```text
doppler-lab terrain-point work/tucson-terrain --latitude 32.30 --longitude -110.80 --microphone-height 0
```

The result is **WGS84 ellipsoid height**, not the DEM's original NAVD88 elevation.
It therefore need not equal an elevation shown in a map application. A zero microphone
height requests bare ground. For an iPad on a table, measure its microphone height
above ground and pass that instead; this tool cannot infer a building floor or roof.

Our downloaded dataset gave about **782.377 m ellipsoid height** at this example point.
That is a reproducibility check for the recorded tile versions, not a surveyed control.

We also compared three explicitly NAD83 sample coordinates against the USGS Elevation
Point Query Service before ellipsoid conversion. Differences were **0.002 m, 1.813 m
and 1.606 m**. The service reported 1-metre source data, while our DEM has approximately
10-metre spacing, so these are consistency checks rather than survey accuracy estimates.
[Recorded inputs and results](https://github.com/ArgeliusLabs/DopplerLab/blob/main/examples/terrain-benchmark.json)
include the source URLs, responses, hashes and library versions.

## 3. Use terrain in broad screening

First prepare an aircraft index as described in the
[broad-search guide](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/BROAD_SEARCH.md).
The terrain bounds must cover every grid node in that index's receiver bounds. Use
`subset-index` when the index covers a larger region than the DEM bundle.

```text
doppler-lab shortlist work/tucson-index/index.sqlite --interval 920 --grid-km 1 --terrain work/tucson-terrain --microphone-height 1.5 --output work/tucson-screen
```

**920 seconds is a hypothetical example.** Replace it with the measured interval between
two supported flyover landmarks and set `--tolerance` from the measurement uncertainty.
Do not pass `--receiver-height` together with `--terrain`. A deliberately flat screen
remains available with `--receiver-height`, but its assumptions are explicit.

Candidate CSV rows now contain each node's actual terrain-derived ellipsoid height.
`screening.json` preserves terrain provenance and the height range. `export-candidate`
uses the selected node's actual height for its local origin and preserves that provenance.

This is still a coarse timing filter. Terrain is sampled at grid nodes; relief between
nodes and curved/noisy trajectories can defeat the approximate cell timing allowance.
Use finer grids and independent checks before excluding an area. Terrain does not fix
missing aircraft, poor ADS-B altitude, unsupported dates or mistaken flyover landmarks.

## 4. Prepare terrain-following local candidates

```text
doppler-lab prepare-observers work/tucson-terrain --bounds 32.27 -110.86 32.37 -110.74 --spacing-m 100 --microphone-height 1.5 --output work/local-receivers
```

This writes:

| File | Purpose |
| --- | --- |
| `observers.csv` | Candidate `east_m,north_m,up_m` coordinates for the local solver |
| `geographic.csv` | The same candidates as latitude, longitude and ellipsoid height |
| `observers.json` | Exact `origin_wgs84`, hashes, preparation settings and terrain provenance |

Without `--origin`, the tool chooses the bounding-box centre with its terrain ground
height. **Import the aircraft tracks using exactly that `origin_wgs84`**, including its
third coordinate. If continuing an `export-candidate` handoff, instead pass its existing
origin explicitly: `--origin LAT LON ELLIPSOID_M`. Do not mix origins.

Place the generated files inside your local case directory. In `case.json`, remove
`grid` and set `"observers": "observers.csv"`. Retain `observers.json` and record its
hash/reference in your case provenance. The solver already hashes `observers.csv`.
Supply the original audio, reviewed flight tracks, actual event windows and clock
bounds using the [investigation workflow](https://github.com/ArgeliusLabs/DopplerLab/blob/main/docs/INVESTIGATION_WORKFLOW.md).
Then run `doppler-lab run case.json --output report`.

The local limit is 20,000 observers within 50 km of one origin. Start coarse, then
prepare smaller candidate regions at finer spacing. The coordinate transform accounts
for Earth curvature; an ENU `up` value is not just elevation minus origin height.

## 5. Test sensitivity and preserve competing answers

Repeat preparation into new directories with supported height offsets, for example
`--height-offset -10` and `--height-offset 10`, and repeat the matching. Use offsets
justified by your DEM/site uncertainties; ±10 m is an example, not a universal error bound.
Keep the same audio evidence and record why bounds or settings changed.

The terrain tests cover interpolation, axes, geoid sign, microphone height, local-frame
conversion, hash failures, nodata, download truncation and propagation into broad-search
candidate heights. The real Tucson terrain run also exercised the existing November 2
flight index with a hypothetical interval. **Neither is a successful geolocation test
of the owner's iPad recording.** A later [original-recording analysis](FIELD_TEST_2026_11.md)
used this terrain and ended with insufficient acoustic evidence.

The Tucson archive check sampled 1,707 terrain nodes, with receiver ellipsoid heights
from 614.932 to 2,729.908 m. It produced 54,200 timing candidates, compared with 51,156
in the earlier zero-height run using the same index and interval/grid/radius settings.
Terrain changed the geometry and candidate set; candidate count is not an accuracy metric.

## Errors and interpretation

| Message or situation | Action |
| --- | --- |
| No supported transformation covers the area | Split into smaller regions; correction operations have geographic limits |
| Outside downloaded terrain bounds | Download a covering region or use a smaller aircraft index/local candidate box |
| Missing terrain/valid neighbours | Preserve the failure; obtain supported coverage rather than substituting zero |
| Hash/size mismatch or missing grid | Restore the original bundle or download again; do not edit its hashes to hide changes |
| Query incomplete or more than 32 tiles | Split the search area; this release performs bounded regional downloads |
| Output exists | Choose a new result folder; previous evidence is preserved |

The stored operation accuracy describes the **coordinate conversion only**. It is not
DEM accuracy, total height uncertainty, or location accuracy. The selected correction
grids follow the source CRS and operation coverage; choosing the newest geoid by name
and relabelling every source as NAD83(2011) would be an unsupported assumption.

Terrain sampling does not simulate acoustic shadowing, canyon reflections, trees,
buildings, wind or refraction. Review these separately. No real-recording accuracy claim
is made by this release.

## Sources and data rights

- [USGS download products and access](https://www.usgs.gov/faqs/what-types-elevation-datasets-are-available-what-formats-do-they-come-and-where-can-i-download)
- [USGS DEM coordinate references](https://www.usgs.gov/faqs/what-projection-horizontal-datum-vertical-datum-and-resolution-a-usgs-digital-elevation-model)
- [National Map API](https://tnmaccess.nationalmap.gov/api/v1/docs)
- [PROJ correction-grid distribution](https://cdn.proj.org/)
- [pyproj explicit transformation selection](https://pyproj4.github.io/pyproj/stable/advanced_examples.html#transformation-group)

3DEP products are public-domain data. Correction grids and software dependencies retain
their own notices; the downloaded bundle contains the NOAA/PROJ-data notice. No terrain
rasters or private recordings are shipped inside the repository or native executable.
