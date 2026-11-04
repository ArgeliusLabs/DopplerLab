import csv
import io
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from doppler_lab.case import digest
from doppler_lab.physics import geodetic_to_enu
from doppler_lab.terrain import (
    SOURCE_CRS,
    TARGET_CRS,
    Terrain,
    bilinear,
    download_terrain,
    fetch_file,
    geographic_grid,
    prepare_observers,
    select_operation,
    select_products,
    write_json,
)


@pytest.fixture
def terrain_bundle(tmp_path):
    # Spaces exercise portable correction-grid paths in the PROJ pipeline.
    root = tmp_path / "fictional terrain"
    (root / "grids").mkdir(parents=True)
    elevation = (400 + 10 * np.arange(64)[:, None] + 4 * np.arange(64)[None, :]).astype("float32")
    with rasterio.open(
        root / "dem.tif",
        "w",
        driver="GTiff",
        width=64,
        height=64,
        count=1,
        dtype="float32",
        crs="EPSG:4269",
        nodata=-9999,
        transform=from_origin(-110.83, 32.33, 0.001, 0.001),
    ) as dst:
        dst.write(elevation, 1)
    with rasterio.open(
        root / "grids/geoid.tif",
        "w",
        driver="GTiff",
        width=8,
        height=8,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(-112, 34, 0.5, 0.5),
    ) as dst:
        dst.write(np.full((8, 8), -30, dtype="float32"), 1)
        dst.update_tags(TYPE="VERTICAL_OFFSET_GEOGRAPHIC_TO_VERTICAL")
        dst.set_band_description(1, "geoid_undulation")

    def record(path):
        return {"name": path.name, "bytes": path.stat().st_size, "sha256": digest(path)}

    info = {
        "schema_version": 1,
        "status": "complete",
        "provider": "fictional test fixture",
        "source_crs": SOURCE_CRS,
        "target_crs": TARGET_CRS,
        "bounds": [32.27, -110.825, 32.325, -110.77],
        "sampling": "bilinear",
        "limitations": ["fictional geoid, not for actual data"],
        "tiles": [record(root / "dem.tif")],
        "operation": {
            "axis_order": "latitude_longitude_height",
            "accuracy_m": 0,
            "pipeline": "+proj=pipeline +step +proj=axisswap +order=2,1 "
            "+step +proj=unitconvert +xy_in=deg +xy_out=rad "
            "+step +proj=vgridshift +grids=geoid.tif +multiplier=1 "
            "+step +proj=unitconvert +xy_in=rad +xy_out=deg "
            "+step +proj=axisswap +order=2,1",
            "grids": [record(root / "grids/geoid.tif")],
        },
    }
    write_json(root / "terrain.json", info)
    return root


def test_pixel_centre_bilinear_and_axis_order(terrain_bundle):
    with rasterio.open(terrain_bundle / "dem.tif") as dataset:
        assert bilinear(dataset, -110.8265, 32.3275) == pytest.approx(432, abs=1e-7)
        assert bilinear(dataset, -110.826, 32.327) == pytest.approx(439, abs=1e-7)
        assert bilinear(dataset, -120, 32) is None


def test_geoid_sign_microphone_and_height_sensitivity(terrain_bundle):
    terrain = Terrain(terrain_bundle)
    # Pixel row 10, column 10: 400+100+40=540 NAVD88; -30 grid -> 510 ellipsoid.
    result = terrain.sample([32.3195], [-110.8195], microphone_height_m=2)
    assert result[0] == pytest.approx(512, abs=1e-6)
    shifted = terrain.sample([32.3195], [-110.8195], 2, 17)
    assert shifted[0] == pytest.approx(529, abs=1e-6)


def test_observers_have_real_3d_geometry_and_preserved_origin(terrain_bundle, tmp_path):
    bounds = [32.29, -110.81, 32.31, -110.79]
    origin = [32.3, -110.8, 750]
    out = tmp_path / "observers"
    result = prepare_observers(terrain_bundle, out, bounds, 500, origin, 2)
    geographic = np.genfromtxt(out / "geographic.csv", delimiter=",", names=True)
    xyz = np.genfromtxt(out / "observers.csv", delimiter=",", skip_header=1)
    expected = geodetic_to_enu(
        geographic["latitude_deg"],
        geographic["longitude_deg"],
        geographic["height_ellipsoid_m"],
        origin,
    )
    np.testing.assert_allclose(xyz, expected)
    assert np.ptp(xyz[:, 2]) > 100
    assert result["origin_wgs84"] == origin
    assert result["observers_sha256"] == digest(out / "observers.csv")
    assert result["terrain"]["microphone_height_m"] == 2


def test_missing_grid_tampering_and_outside_coverage_are_errors(terrain_bundle):
    terrain = Terrain(terrain_bundle)
    with pytest.raises(ValueError, match="outside"):
        terrain.sample([35], [-110])
    with (terrain_bundle / "dem.tif").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="hash/size"):
        Terrain(terrain_bundle)
    (terrain_bundle / "grids/geoid.tif").unlink()
    assert not (terrain_bundle / "grids/geoid.tif").exists()


def test_missing_grid_has_no_network_or_zero_height_fallback(terrain_bundle):
    (terrain_bundle / "grids/geoid.tif").unlink()
    with pytest.raises(ValueError, match="Missing case input"):
        Terrain(terrain_bundle)


def test_nodata_does_not_become_sea_level(terrain_bundle):
    with rasterio.open(terrain_bundle / "dem.tif", "r+") as dataset:
        a = dataset.read(1)
        a[10, 10] = -9999
        dataset.write(a, 1)
    path = terrain_bundle / "terrain.json"
    info = json.loads(path.read_text())
    info["tiles"][0].update(
        bytes=(terrain_bundle / "dem.tif").stat().st_size, sha256=digest(terrain_bundle / "dem.tif")
    )
    write_json(path, info)
    with pytest.raises(ValueError, match="Missing terrain"):
        Terrain(terrain_bundle).sample([32.3195], [-110.8195])


def test_grid_limit_and_unsupported_region():
    with pytest.raises(ValueError, match="More than"):
        geographic_grid([32, -111, 33, -110], 10)
    with pytest.raises(ValueError, match="contiguous US"):
        geographic_grid([40, 10, 41, 11], 1000)


def product():
    return {
        "downloadURL": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/"
        "TIFF/historical/n33w111/USGS_13_n33w111_20261027.tif",
        "format": "GeoTIFF",
        "sizeInBytes": 100,
        "boundingBox": {"minY": 32, "minX": -111, "maxY": 33, "maxX": -110},
        "title": "test",
        "sourceId": "test",
    }


def test_download_selection_rejects_truncation_duplicate_tiles_and_foreign_urls():
    item = product()
    bounds = [32.2, -110.9, 32.4, -110.7]
    assert select_products({"items": [item], "total": 1}, bounds)[0]["expected_bytes"] == 100
    with pytest.raises(ValueError, match="incomplete"):
        select_products({"items": [item], "total": 101}, bounds)
    with pytest.raises(ValueError, match="Multiple"):
        select_products({"items": [item, item], "total": 2}, bounds)
    item["downloadURL"] = "https://example.org/file.tif"
    with pytest.raises(ValueError, match="Unexpected"):
        select_products({"items": [item], "total": 1}, bounds)


def test_failed_download_never_becomes_final_file(tmp_path, monkeypatch):
    class Response(io.BytesIO):
        headers = {"Content-Length": "12"}

        def geturl(self):
            return "https://cdn.proj.org/grid.tif"

    monkeypatch.setattr("doppler_lab.terrain.open_url", lambda _: Response(b"short"))
    path = tmp_path / "grid.tif"
    with pytest.raises(ValueError, match="Incomplete"):
        fetch_file("https://cdn.proj.org/grid.tif", path, {"received_bytes": 0, "max_bytes": 100})
    assert not path.exists()


def test_declared_crs_selects_recordable_non_ballpark_height_operation():
    operation = select_operation([32.1, -111.15, 32.55, -110.55])
    assert operation["accuracy_m"] >= 0
    assert "vgridshift" in operation["pipeline"]
    assert "ballpark" not in operation["description"].lower()
    assert operation["grids"]
    assert all(g["url"] == "https://cdn.proj.org/" + g["name"] for g in operation["grids"])


def test_complete_downloader_keeps_a_usable_offline_bundle(terrain_bundle, tmp_path, monkeypatch):
    original = json.loads((terrain_bundle / "terrain.json").read_text())
    tile = product()
    tile["sizeInBytes"] = (terrain_bundle / "dem.tif").stat().st_size
    operation = original["operation"]
    operation["grids"][0]["url"] = "https://cdn.proj.org/geoid.tif"
    monkeypatch.setattr("doppler_lab.terrain.select_operation", lambda _: operation)
    files = {
        tile["downloadURL"]: (terrain_bundle / "dem.tif").read_bytes(),
        "https://cdn.proj.org/geoid.tif": (terrain_bundle / "grids/geoid.tif").read_bytes(),
        "https://cdn.proj.org/us_noaa_README.txt": b"Fictional grid notice",
    }

    class Response(io.BytesIO):
        def __init__(self, url):
            self.url = url
            raw = json.dumps({"total": 1, "items": [tile]}).encode() if "?" in url else files[url]
            self.headers = {"Content-Length": str(len(raw))}
            super().__init__(raw)

        def geturl(self):
            return self.url

    monkeypatch.setattr("doppler_lab.terrain.open_url", Response)
    output = tmp_path / "download"
    result = download_terrain([32.29, -110.81, 32.31, -110.79], output, max_gb=0.06)
    assert result["status"] == "complete"
    assert result["query_sha256"] == digest(output / "usgs-query.json")
    assert result["downloaded_bytes"] == sum(len(value) for value in files.values())
    assert Terrain(output).sample([32.30], [-110.80])[0] > 0


def test_broad_search_uses_terrain_and_exports_its_actual_height(terrain_bundle, tmp_path):
    from test_broad import BOUNDS, make_archive

    from doppler_lab.broad import build_index, export_candidate, shortlist

    parts = make_archive(tmp_path)
    build_index(parts, tmp_path / "index", BOUNDS, "2026-11-02T12:00:00Z", "2026-11-02T13:00:00Z")
    index = tmp_path / "index/index.sqlite"
    screen = tmp_path / "screen"
    result = shortlist(index, screen, 920, grid_km=1, terrain_path=terrain_bundle)
    assert result["status"] == "complete"
    assert result["receiver_height_m"] is None
    assert result["terrain"]["terrain_manifest_sha256"] == digest(terrain_bundle / "terrain.json")
    with (screen / "candidates.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len({r["receiver_height_m"] for r in rows}) > 1
    first = rows[0]
    expected = Terrain(terrain_bundle).sample(
        [float(first["latitude_deg"])], [float(first["longitude_deg"])]
    )[0]
    assert float(first["receiver_height_m"]) == pytest.approx(expected)
    handoff = export_candidate(index, screen, int(first["candidate_id"]), tmp_path / "handoff")
    assert handoff["origin_wgs84"][2] == pytest.approx(expected)
    assert handoff["terrain"] == result["terrain"]
