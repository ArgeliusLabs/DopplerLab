"""Auditable USGS 3DEP downloads and offline terrain-to-WGS84 preparation.

The first provider is the contiguous-US 1/3 arc-second NAD83/NAVD88 product.
Missing pixels, incompatible references and absent correction grids are errors.
"""

import csv
import hashlib
import json
import math
import re
import shutil
import time
import warnings
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urlencode, urlparse

import numpy as np
import pyproj
import rasterio
from pyproj.enums import TransformDirection
from pyproj.transformer import AreaOfInterest, TransformerGroup
from rasterio.windows import Window

from . import __version__
from .adsb import new_folder, number, utc
from .archive import open_url
from .case import digest, local_path
from .physics import geodetic_to_enu

DATASET = "National Elevation Dataset (NED) 1/3 arc-second Current"
API = "https://tnmaccess.nationalmap.gov/api/v1/products"
SOURCE_CRS = "EPSG:5498"  # NAD83 + NAVD88 height; source axis order latitude, longitude.
TARGET_CRS = "EPSG:4979"


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def check_bounds(bounds):
    if len(bounds) != 4 or not all(number(v) for v in bounds):
        raise ValueError("Terrain bounds need finite SOUTH WEST NORTH EAST coordinates.")
    s, w, n, e = bounds
    if not (24 <= s < n <= 50 and -125 <= w < e <= -66):
        raise ValueError("Automatic terrain support is currently limited to the contiguous US.")
    return list(bounds)


def contains(outer, inner, epsilon=0):
    s, w, n, e = outer
    a, b, c, d = inner
    return s - epsilon <= a and w - epsilon <= b and n + epsilon >= c and e + epsilon >= d


def geographic_grid(bounds, spacing_m, limit=20_000):
    s, w, n, e = check_bounds(bounds)
    if not number(spacing_m) or not 10 <= spacing_m <= 20_000:
        raise ValueError("Terrain grid spacing must be 10–20000 metres.")
    rows, count = [], 0
    for latitude in np.unique(np.append(np.arange(s, n, spacing_m / 111320), n)):
        longitudes = np.unique(
            np.append(np.arange(w, e, spacing_m / (111320 * math.cos(math.radians(latitude)))), e)
        )
        count += len(longitudes)
        if count > limit:
            raise ValueError(
                f"More than {limit:,} terrain points; use a smaller area or wider grid."
            )
        rows.append(np.column_stack((np.full(len(longitudes), latitude), longitudes)))
    return np.concatenate(rows)


def select_products(data, bounds):
    """Only complete current queries, known USGS GeoTIFFs and unique tile identities."""
    items = data.get("items", [])
    if data.get("errors") or data.get("total") != len(items) or not items:
        raise ValueError("USGS query is empty, incomplete or has errors; reduce the region.")
    selected = {}
    for item in items:
        url = item.get("downloadURL", "")
        parsed = urlparse(url)
        match = re.fullmatch(
            r"/StagedProducts/Elevation/13/TIFF/(?:historical|current)/(n\d{2}w\d{3})/"
            r"(USGS_13_\1(?:_\d{8})?\.tif)",
            parsed.path,
        )
        if parsed.scheme != "https" or parsed.netloc != "prd-tnm.s3.amazonaws.com" or not match:
            raise ValueError("Unexpected USGS DEM URL; inspect the provider metadata.")
        if parsed.query or parsed.fragment or item.get("format") != "GeoTIFF":
            raise ValueError("Unexpected DEM format or download URL.")
        size = item.get("sizeInBytes")
        if not number(size) or size <= 0 or int(size) != size:
            raise ValueError("USGS must provide a positive DEM byte count.")
        box = item["boundingBox"]
        footprint = [box["minY"], box["minX"], box["maxY"], box["maxX"]]
        if not all(number(v) for v in footprint):
            raise ValueError("Invalid DEM footprint.")
        s, w, n, e = bounds
        if footprint[2] <= s or footprint[0] >= n or footprint[3] <= w or footprint[1] >= e:
            continue
        tile = match[1]
        if tile in selected:
            raise ValueError("Multiple current versions of one DEM tile; inspect the query.")
        selected[tile] = {
            "name": match[2],
            "url": url,
            "expected_bytes": int(size),
            "bounds": footprint,
            "title": item["title"],
            "source_id": item["sourceId"],
            "metadata_url": item.get("metaUrl"),
            "publication_date": item.get("publicationDate"),
        }
    if not selected or len(selected) > 32:
        raise ValueError("Need 1–32 DEM tiles; split larger areas into regional downloads.")
    return [selected[key] for key in sorted(selected)]


def select_operation(bounds):
    """Choose an explicit non-ballpark operation covering the entire requested region."""
    s, w, n, e = bounds
    pyproj.network.set_network_enabled(False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        group = TransformerGroup(
            SOURCE_CRS,
            TARGET_CRS,
            allow_ballpark=False,
            area_of_interest=AreaOfInterest(w, s, e, n),
        )
    candidates = []
    for operation in [*group.transformers, *group.unavailable_operations]:
        area = operation.area_of_use
        if area is None or not contains([area.south, area.west, area.north, area.east], bounds):
            continue
        definition = operation.to_proj4()
        if not definition or "vgridshift" not in definition or operation.accuracy < 0:
            continue
        grids = getattr(operation, "grids", None)
        if grids is None:
            grids = [g for op in operation.operations for g in op.grids]
        if not grids or any(not g.open_license or not g.direct_download for g in grids):
            continue
        records = {}
        for grid in grids:
            if not re.fullmatch(r"[A-Za-z0-9_]+\.tif", grid.short_name):
                raise ValueError("Unexpected coordinate-correction grid name.")
            if grid.url != f"https://cdn.proj.org/{grid.short_name}":
                raise ValueError("Unexpected coordinate-correction grid URL.")
            records[grid.short_name] = {"name": grid.short_name, "url": grid.url}
        candidates.append(
            {
                "description": getattr(operation, "description", operation.name),
                "accuracy_m": operation.accuracy,
                "pipeline": definition,
                "axis_order": "latitude_longitude_height",
                "grids": list(records.values()),
                "area": [area.south, area.west, area.north, area.east],
            }
        )
    if not candidates:
        raise ValueError(
            "No supported height transformation covers this area; use smaller regions."
        )
    return min(candidates, key=lambda op: (op["accuracy_m"], len(op["grids"]), op["description"]))


def fetch_file(url, path, budget, expected=None, progress=None):
    """Stream into a fresh partial file; never treat a truncated download as complete."""
    temporary = path.with_name(path.name + ".partial")
    count, checksum = 0, hashlib.sha256()
    with open_url(url) as response, temporary.open("xb") as stream:
        final = urlparse(response.geturl())
        initial = urlparse(url)
        if final.scheme != "https" or final.netloc != initial.netloc:
            raise ValueError("Unexpected download redirect.")
        declared = response.headers.get("Content-Length")
        if declared and expected is not None and int(declared) != expected:
            raise ValueError("DEM size changed after the query; obtain new metadata.")
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            budget["received_bytes"] += len(chunk)
            if budget["received_bytes"] > budget["max_bytes"] or (expected and count > expected):
                raise ValueError("Terrain download exceeded its byte budget.")
            stream.write(chunk)
            checksum.update(chunk)
            if progress:
                progress({"file": path.name, **budget})
        if (expected is not None and count != expected) or (declared and count != int(declared)):
            raise ValueError("Incomplete terrain download.")
    if count == 0:
        raise ValueError("Empty terrain download.")
    temporary.rename(path)
    return {"bytes": count, "sha256": checksum.hexdigest()}


def bind_pipeline(operation, root):
    """Bind recorded correction grids to this bundle, never to a global/network cache."""
    pipeline = operation["pipeline"]
    records = {g["name"]: g for g in operation["grids"]}
    seen = set()

    def replace(match):
        name = match[1]
        if name not in records or not re.fullmatch(r"[A-Za-z0-9_]+\.tif", name):
            raise ValueError("Pipeline references an unrecorded or optional correction grid.")
        path = local_path(root, "grids/" + name)
        if '"' in str(path):
            raise ValueError("Terrain paths must not contain double quotes.")
        seen.add(name)
        return '+grids="' + path.as_posix() + '"'

    pipeline = re.sub(r"\+grids=([^\s]+)", replace, pipeline)
    if seen != set(records) or "vgridshift" not in pipeline:
        raise ValueError("Terrain height conversion must use its recorded correction grids.")
    pyproj.network.set_network_enabled(False)
    return pyproj.Transformer.from_pipeline(pipeline)


def download_terrain(bounds, output, max_gb=2, progress=None):
    bounds = check_bounds(bounds)
    if not number(max_gb) or not 0 < max_gb <= 30:
        raise ValueError("Terrain download budget must be in (0, 30] decimal GB.")
    s, w, n, e = bounds
    # A small margin covers datum shifts and bilinear interpolation at area boundaries.
    query = (
        API
        + "?"
        + urlencode(
            {
                "datasets": DATASET,
                "bbox": f"{w - 0.002},{s - 0.002},{e + 0.002},{n + 0.002}",
                "prodFormats": "GeoTIFF",
                "max": 100,
            }
        )
    )
    with open_url(query) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("USGS query metadata exceeds 5 MB.")
    products = select_products(json.loads(raw), [s - 0.002, w - 0.002, n + 0.002, e + 0.002])
    expected = sum(p["expected_bytes"] for p in products)
    if expected + 50_000_000 > max_gb * 1e9:
        raise ValueError(
            f"DEMs need {expected / 1e9:.3f} GB plus correction grids; increase --max-gb."
        )
    operation = select_operation(bounds)
    output = new_folder(output)
    (output / "grids").mkdir()
    if shutil.disk_usage(output).free < max_gb * 1e9 + 200_000_000:
        raise ValueError("Insufficient free space for the terrain budget plus 200 MB headroom.")
    (output / "usgs-query.json").write_bytes(raw)
    info = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "downloading",
        "provider": "USGS 3DEP",
        "dataset": DATASET,
        "bounds": bounds,
        "source_crs": SOURCE_CRS,
        "target_crs": TARGET_CRS,
        "source_height_units": "metres",
        "sampling": "bilinear; no nodata substitution",
        "query_url": query,
        "query_sha256": hashlib.sha256(raw).hexdigest(),
        "created_utc": utc(),
        "tiles": products,
        "operation": operation,
        "versions": {
            "pyproj": pyproj.__version__,
            "proj": pyproj.proj_version_str,
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
        },
        "licenses": [
            "USGS 3DEP: public domain",
            "Correction grids: see PROJ-data us_noaa_README.txt",
        ],
        "limitations": [
            "Terrain elevations do not model acoustic blockage, reflections, wind or refraction.",
            "Operation accuracy describes the coordinate transformation, not DEM or location accuracy.",
            "The DEM represents bare ground; specify the microphone height separately.",
        ],
    }
    started = time.monotonic()
    budget = {"received_bytes": 0, "max_bytes": int(max_gb * 1e9)}
    try:
        for record in operation["grids"]:
            record.update(
                fetch_file(
                    record["url"], output / "grids" / record["name"], budget, progress=progress
                )
            )
        notice = "https://cdn.proj.org/us_noaa_README.txt"
        info["grid_notice"] = {
            "name": "grids/us_noaa_README.txt",
            "url": notice,
            **fetch_file(notice, output / "grids/us_noaa_README.txt", budget),
        }
        bind_pipeline(operation, output)
        for record in products:
            record.update(
                fetch_file(
                    record["url"],
                    output / record["name"],
                    budget,
                    record["expected_bytes"],
                    progress,
                )
            )
            with rasterio.open(output / record["name"]) as dataset:
                validate_raster(dataset)
                record["raster"] = {
                    "crs": dataset.crs.to_wkt(),
                    "shape": list(dataset.shape),
                    "resolution_deg": list(dataset.res),
                    "nodata": dataset.nodata,
                }
        info["status"] = "complete"
    except BaseException as error:
        info["status"], info["error"] = "failed", str(error)
        raise
    finally:
        info["elapsed_s"] = round(time.monotonic() - started, 3)
        info["downloaded_bytes"] = budget["received_bytes"]
        write_json(output / "terrain.json", info)
    return info


def validate_raster(dataset):
    crs = pyproj.CRS(dataset.crs)
    if (
        crs.to_2d().to_epsg() != 4269
        or dataset.count != 1
        or dataset.transform.b != 0
        or dataset.transform.d != 0
        or dataset.transform.a <= 0
        or dataset.transform.e >= 0
    ):
        raise ValueError("Expected a north-up, single-band USGS NAD83 DEM.")
    if crs.is_compound and crs.sub_crs_list[-1].to_epsg() != 5703:
        raise ValueError("DEM has a vertical reference other than NAVD88.")
    if dataset.units[0] not in (None, "m", "metre", "meter"):
        raise ValueError("DEM must contain metre elevations.")
    if dataset.scales != (1.0,) or dataset.offsets != (0.0,):
        raise ValueError("Scaled DEM values are not supported.")


def bilinear(dataset, x, y):
    """Sample pixel centres; require all four neighbours to be valid."""
    inverse = ~dataset.transform
    column = inverse.a * x + inverse.b * y + inverse.c
    row = inverse.d * x + inverse.e * y + inverse.f
    column, row = column - 0.5, row - 0.5
    c, r = math.floor(column), math.floor(row)
    if not (0 <= c < dataset.width - 1 and 0 <= r < dataset.height - 1):
        return None
    values = dataset.read(1, window=Window(c, r, 2, 2), masked=True)
    if np.ma.getmaskarray(values).any() or not np.isfinite(values).all():
        return None
    a, b = column - c, row - r
    return float(
        values[0, 0] * (1 - a) * (1 - b)
        + values[0, 1] * a * (1 - b)
        + values[1, 0] * (1 - a) * b
        + values[1, 1] * a * b
    )


class Terrain:
    """Verify the bundle once, then sample it without network requests."""

    def __init__(self, folder):
        self.root = Path(folder).resolve()
        path = self.root / "terrain.json"
        self.info = json.loads(path.read_text(encoding="utf-8"))
        info = self.info
        if (
            info.get("status") != "complete"
            or info.get("schema_version") != 1
            or info.get("source_crs") != SOURCE_CRS
            or info.get("target_crs") != TARGET_CRS
        ):
            raise ValueError("Use a completed supported terrain bundle.")
        check_bounds(info["bounds"])
        if info["operation"]["axis_order"] != "latitude_longitude_height":
            raise ValueError("Unexpected terrain conversion axis order.")
        self.sha256 = digest(path)
        records = [(r, r["name"]) for r in info["tiles"]]
        records.extend((g, "grids/" + g["name"]) for g in info["operation"]["grids"])
        for record, name in records:
            source = local_path(self.root, name)
            if source.stat().st_size != record["bytes"] or digest(source) != record["sha256"]:
                raise ValueError(f"Terrain input hash/size mismatch: {name}")
        self.transformer = bind_pipeline(info["operation"], self.root)

    def sample(self, latitudes, longitudes, microphone_height_m=1.5, height_offset_m=0):
        lat, lon = np.broadcast_arrays(np.asarray(latitudes, float), np.asarray(longitudes, float))
        if lat.ndim != 1 or not len(lat) or not np.isfinite([lat, lon]).all():
            raise ValueError("Supply finite one-dimensional terrain coordinates.")
        if (
            not number(microphone_height_m)
            or not 0 <= microphone_height_m <= 200
            or not number(height_offset_m)
            or abs(height_offset_m) > 1000
        ):
            raise ValueError("Use microphone height 0–200 m and sensitivity offset within ±1000 m.")
        if not contains(self.info["bounds"], [lat.min(), lon.min(), lat.max(), lon.max()], 1e-9):
            raise ValueError("Candidate points extend outside the downloaded terrain bounds.")
        height = np.zeros(len(lat))
        with ExitStack() as stack:
            datasets = [
                stack.enter_context(rasterio.open(local_path(self.root, t["name"])))
                for t in self.info["tiles"]
            ]
            for dataset in datasets:
                validate_raster(dataset)
            # Iterate the inverse horizontal mapping at the estimated physical height.
            for _ in range(3):
                sy, sx, _ = self.transformer.transform(
                    lat, lon, height, direction=TransformDirection.INVERSE, errcheck=True
                )
                ground = []
                for x, y in zip(sx, sy, strict=True):
                    value = next(
                        (v for d in datasets if (v := bilinear(d, x, y)) is not None), None
                    )
                    if value is None:
                        raise ValueError(f"Missing terrain/valid neighbours at {y:.6f}, {x:.6f}.")
                    ground.append(value)
                out_lat, out_lon, height = self.transformer.transform(sy, sx, ground, errcheck=True)
                height = np.asarray(height)
            if (
                not np.isfinite(height).all()
                or np.max(np.abs(out_lat - lat)) > 1e-7
                or np.max(np.abs(out_lon - lon)) > 1e-7
            ):
                raise ValueError("Terrain coordinate conversion did not converge.")
        return height + microphone_height_m + height_offset_m

    def provenance(self, microphone_height_m, height_offset_m):
        return {
            "terrain_manifest_sha256": self.sha256,
            "provider": self.info["provider"],
            "source_crs": SOURCE_CRS,
            "target_crs": TARGET_CRS,
            "operation": self.info["operation"],
            "tiles": self.info["tiles"],
            "sampling": self.info["sampling"],
            "microphone_height_m": microphone_height_m,
            "height_offset_m": height_offset_m,
            "limitations": self.info["limitations"],
        }


def prepare_observers(
    folder, output, bounds, spacing_m, origin=None, microphone_height_m=1.5, height_offset_m=0
):
    geo = geographic_grid(bounds, spacing_m)
    terrain = Terrain(folder)
    heights = terrain.sample(geo[:, 0], geo[:, 1], microphone_height_m, height_offset_m)
    if origin is None:
        s, w, n, e = bounds
        lat, lon = (s + n) / 2, (w + e) / 2
        origin = [lat, lon, float(terrain.sample([lat], [lon], 0)[0])]
    xyz = geodetic_to_enu(geo[:, 0], geo[:, 1], heights, origin)
    if np.max(np.linalg.norm(xyz, axis=1)) > 50_000:
        raise ValueError("Local observers must be within 50 km of their origin; split the region.")
    output = new_folder(output)
    with (output / "observers.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["east_m", "north_m", "up_m"])
        writer.writerows(xyz)
    with (output / "geographic.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["latitude_deg", "longitude_deg", "height_ellipsoid_m"])
        writer.writerows(np.column_stack((geo, heights)))
    info = {
        "schema_version": 1,
        "tool_version": __version__,
        "status": "complete",
        "bounds": list(bounds),
        "spacing_m": spacing_m,
        "origin_wgs84": list(origin),
        "observer_count": len(xyz),
        "height_range_m": [float(heights.min()), float(heights.max())],
        "terrain": terrain.provenance(microphone_height_m, height_offset_m),
        "observers_sha256": digest(output / "observers.csv"),
        "geographic_sha256": digest(output / "geographic.csv"),
        "next_steps": [
            "Use this exact origin when importing aircraft tracks.",
            "Set observers in case.json to observers.csv instead of grid.",
        ],
    }
    write_json(output / "observers.json", info)
    return info
