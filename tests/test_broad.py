import csv
import gzip
import io
import json
import tarfile
from collections import Counter

import numpy as np
import pytest
from scipy.spatial import cKDTree

from doppler_lab.adsb import capture_points, trace_points
from doppler_lab.archive import PartReader, archive_traces, validate_parts
from doppler_lab.broad import (
    build_index,
    export_candidate,
    filter_candidates,
    open_index,
    passages,
    shortlist,
    subset_index,
)
from doppler_lab.case import digest, load_tracks
from doppler_lab.importers import parse_utc
from doppler_lab.physics import geodetic_to_ecef

EPOCH = parse_utc("2026-11-02T12:00:00Z")
BOUNDS = [32.29, -110.81, 32.31, -110.79]


def trace(icao, offset=0, northbound=False, geometric=True):
    points = []
    for t in range(0, 182, 2):
        distance = (t - 90) * 80
        lat = 32.3 + (distance / 110900 if northbound else 0)
        lon = -110.8 + (0 if northbound else distance / (111320 * np.cos(np.deg2rad(32.3))))
        points.append(
            [
                t + offset,
                lat,
                lon,
                4500,
                155,
                0,
                0,
                0,
                None,
                "adsb_icao",
                1400 / 0.3048 if geometric else None,
            ]
        )
    return {"icao": icao, "timestamp": EPOCH, "trace": points}


def make_archive(tmp_path):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:
        for icao, offset, north, height in [
            ("a00001", 0, False, True),
            ("a00002", 920, True, True),
            ("a00003", 0, False, False),
        ]:
            # Real readsb archives use gzip content even in .json-named members.
            body = gzip.compress(json.dumps(trace(icao, offset, north, height)).encode())
            member = tarfile.TarInfo(f"./traces/01/trace_full_{icao}.json")
            member.size = len(body)
            archive.addfile(member, io.BytesIO(body))
        link = tarfile.TarInfo("./traces/01/trace_full_ffffff.json")
        link.type = tarfile.SYMTYPE
        link.linkname = "../../outside"
        archive.addfile(link)
    data = raw.getvalue()
    a, b = tmp_path / "day.tar.aa", tmp_path / "day.tar.ab"
    a.write_bytes(data[:317])
    b.write_bytes(data[317:])
    return [a, b]


@pytest.fixture
def indexed(tmp_path):
    parts = make_archive(tmp_path)
    folder = tmp_path / "index"
    result = build_index(parts, folder, BOUNDS, "2026-11-02T12:00:00Z", "2026-11-02T13:00:00Z")
    return folder / "index.sqlite", result


def test_split_stream_and_gzip_magic(tmp_path):
    parts = make_archive(tmp_path)
    counts = Counter()
    records = [(name, list(data["trace"])) for name, data in archive_traces(parts, counts)]
    assert len(records) == 3
    assert [p["sha256"] for p in counts["input_parts"]] == [digest(p) for p in parts]
    assert not (tmp_path / "outside").exists()
    with PartReader(parts) as stream:
        assert stream.read(100) == parts[0].read_bytes()[:100]
    with pytest.raises(ValueError, match="order"):
        validate_parts(parts[::-1])
    with pytest.raises(ValueError, match="order"):
        validate_parts([parts[0], tmp_path / "day.tar.ac"])
    path = tmp_path / "trace.json"
    path.write_bytes(gzip.compress(json.dumps(trace("a00001")).encode()))
    decoded = list(trace_points(path, Counter()))
    assert decoded[0]["height_ft"] * 0.3048 == pytest.approx(1400)
    assert decoded[0]["time"] == EPOCH


def test_archive_index_rejects_pressure_height_and_keeps_provenance(indexed):
    path, result = indexed
    assert result["status"] == "complete"
    assert result["counts"]["segments"] == 2
    assert result["counts"]["missing_or_invalid_geometric_height"] == 91
    assert result["index_sha256"] == digest(path)
    db, metadata = open_index(path)
    assert db.execute("SELECT COUNT(*) FROM segments").fetchone()[0] == 2
    assert metadata["bounds"] == BOUNDS
    db.close()


def test_retarded_cpa_for_independent_geographic_flyby():
    data = trace("a00001")
    points = np.array([[EPOCH + p[0], p[1], p[2], p[10] * 0.3048] for p in data["trace"]])
    receiver = geodetic_to_ecef([32.3], [-110.8], [400])
    budget = Counter(max_evaluations=10000)
    found = list(passages(points, cKDTree(receiver), receiver, 10000, 25, 300, 343, budget))
    assert len(found) == 1
    _, arrival, distance, speed = found[0]
    assert distance == pytest.approx(1000, abs=0.01)
    assert arrival == pytest.approx(EPOCH + 90 + 1000 / 343, abs=0.01)
    assert 78 < speed < 82


def test_two_event_candidate_survives_and_exports_local_tracks(indexed, tmp_path):
    path, _ = indexed
    folder = tmp_path / "screen"
    result = shortlist(path, folder, 920, tolerance_s=1, grid_km=1, receiver_height_m=400)
    assert result["status"] == "complete"
    assert result["accepted_location"] is False
    with (folder / "candidates.csv").open() as stream:
        candidates = list(csv.DictReader(stream))
    assert candidates
    assert {(r["icao_a"], r["icao_b"]) for r in candidates} == {("a00001", "a00002")}
    best = min(
        candidates,
        key=lambda r: abs(float(r["latitude_deg"]) - 32.3) + abs(float(r["longitude_deg"]) + 110.8),
    )
    assert abs(float(best["latitude_deg"]) - 32.3) < 0.005
    handoff = export_candidate(path, folder, int(best["candidate_id"]), tmp_path / "local")
    assert handoff["accepted_location"] is False
    assert len(load_tracks(tmp_path / "local" / "tracks.csv", 5)) == 2
    assert handoff["max_track_gap_s"] == 2


def test_wrong_interval_does_not_pass(indexed, tmp_path):
    path, _ = indexed
    result = shortlist(
        path, tmp_path / "wrong", 500, tolerance_s=1, grid_km=1, receiver_height_m=400
    )
    assert result["counts"].get("candidates", 0) == 0


def test_budget_exhaustion_is_failed_not_a_complete_shortlist(indexed, tmp_path):
    path, _ = indexed
    folder = tmp_path / "budget"
    with pytest.raises(ValueError, match="budget"):
        shortlist(path, folder, 920, grid_km=1, max_evaluations=1)
    result = json.loads((folder / "screening.json").read_text())
    assert result["status"] == "failed"
    with pytest.raises(ValueError, match="completed"):
        export_candidate(path, folder, 1, tmp_path / "bad-export")


def test_modified_candidates_cannot_be_handed_off(indexed, tmp_path):
    path, _ = indexed
    folder = tmp_path / "screen"
    shortlist(path, folder, 920, grid_km=1)
    with (folder / "candidates.csv").open("a") as stream:
        stream.write("tampered\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        export_candidate(path, folder, 1, tmp_path / "bad-export")


def test_capture_position_time_uses_provider_age_and_hash(tmp_path):
    import hashlib

    body = json.dumps(
        {
            "now": EPOCH * 1000,
            "ac": [
                {
                    "hex": "a00001",
                    "seen_pos": 1.2,
                    "lat": 32.3,
                    "lon": -110.8,
                    "alt_geom": 4000,
                    "type": "adsb_icao",
                    "alt_baro": 3800,
                }
            ],
        }
    )
    path = tmp_path / "capture.jsonl"
    path.write_text(
        json.dumps({"body_utf8": body, "body_sha256": hashlib.sha256(body.encode()).hexdigest()})
        + "\n"
    )
    points = list(capture_points(path, Counter()))
    assert points[0]["time"] == pytest.approx(EPOCH - 1.2)
    path.write_text(json.dumps({"body_utf8": body, "body_sha256": "wrong"}) + "\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        list(capture_points(path, Counter()))


def test_repeated_flybys_remain_separate_passages():
    first = trace("a00001")["trace"]
    second = trace("a00001", 360)["trace"]
    # Return over the same receiver after a long turn, represented by a separate continuous leg.
    receiver = geodetic_to_ecef([32.3], [-110.8], [400])
    found = []
    for leg in [first, second]:
        points = np.array([[EPOCH + p[0], p[1], p[2], p[10] * 0.3048] for p in leg])
        found.extend(
            passages(
                points,
                cKDTree(receiver),
                receiver,
                10000,
                25,
                300,
                343,
                Counter(max_evaluations=10000),
            )
        )
    assert len(found) == 2
    assert found[1][1] - found[0][1] == pytest.approx(360, abs=0.001)


def test_truncated_archive_cannot_be_used_as_a_complete_index(tmp_path):
    parts = make_archive(tmp_path)
    parts[1].write_bytes(parts[1].read_bytes()[:700])
    folder = tmp_path / "truncated"
    with pytest.raises((ValueError, tarfile.ReadError, EOFError)):
        build_index(parts, folder, BOUNDS, "2026-11-02T12:00:00Z", "2026-11-02T13:00:00Z")
    assert json.loads((folder / "index.json").read_text())["status"] == "failed"
    with pytest.raises(ValueError, match="incomplete"):
        open_index(folder / "index.sqlite")


def test_download_size_hash_and_budget_are_checked(tmp_path, monkeypatch):
    from doppler_lab import archive

    tag = "v2026.11.02-planes-readsb-prod-0"
    body = b"fictional tar bytes"
    url = f"https://github.com/adsblol/globe_history_2026/releases/download/{tag}/{tag}.tar"
    release = {
        "html_url": f"https://github.com/adsblol/globe_history_2026/releases/tag/{tag}",
        "assets": [
            {
                "name": tag + ".tar",
                "size": len(body),
                "browser_download_url": url,
                "digest": "sha256:wrong",
            }
        ],
    }

    def response(requested):
        return io.BytesIO(json.dumps(release).encode() if "api.github.com" in requested else body)

    monkeypatch.setattr(archive, "open_url", response)
    with pytest.raises(ValueError, match="budget"):
        archive.download_day("2026-11-02", tmp_path / "too-big", max_gb=1e-10)
    with pytest.raises(ValueError, match="digest"):
        archive.download_day("2026-11-02", tmp_path / "bad-digest")
    assert not (tmp_path / "bad-digest" / (tag + ".tar")).exists()
    assert json.loads((tmp_path / "bad-digest/download.json").read_text())["status"] == "failed"
    release["assets"][0]["digest"] = None
    good = archive.download_day("2026-11-02", tmp_path / "good")
    assert good["status"] == "complete"
    assert good["parts"][0]["sha256"] == digest(tmp_path / "good" / (tag + ".tar"))


def test_smaller_region_reuses_source_evidence_without_reparsing_archive(indexed, tmp_path):
    source, _ = indexed
    bounds = [32.295, -110.805, 32.305, -110.795]
    result = subset_index(source, tmp_path / "subset", bounds)
    assert result["status"] == "complete"
    assert result["bounds"] == bounds
    assert result["source_index_sha256"] == digest(source)
    assert result["counts"]["segments"] == 2
    with pytest.raises(ValueError, match="inside"):
        subset_index(source, tmp_path / "outside", [30, -112, 34, -110])


def test_audio_constraint_filter_preserves_truth_ids_and_export(indexed, tmp_path):
    path, _ = indexed
    shortlist(path, tmp_path / "screen", 920, grid_km=1, receiver_height_m=400)
    result = filter_candidates(
        tmp_path / "screen", tmp_path / "filtered", [70, 90], [70, 90], [800, 1500], [800, 1500]
    )
    assert result["status"] == "complete" and result["counts"]["candidates"] > 0
    assert result["accepted_location"] is False
    with (tmp_path / "filtered/candidates.csv").open() as stream:
        first = next(csv.DictReader(stream))
    exported = export_candidate(
        path, tmp_path / "filtered", int(first["candidate_id"]), tmp_path / "filtered-handoff"
    )
    assert len(exported["track_ids"]) == 2
    wrong = filter_candidates(
        tmp_path / "screen",
        tmp_path / "wrong-filter",
        [180, 220],
        [70, 90],
        [800, 1500],
        [800, 1500],
    )
    assert wrong["counts"]["candidates"] == 0
