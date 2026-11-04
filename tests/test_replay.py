import gzip
import json
import urllib.error
from collections import Counter
from datetime import UTC, datetime

import numpy as np
import pytest

from doppler_lab.adsb import normalize
from doppler_lab.replay import MAGIC, WindowFetcher, decode_body, download_window, replay_candidates


def epoch(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp()


def heatmap(stamps, ident=0xA00001):
    rows = [[0, 0, 0, 0]]  # Optional prefix index is not a time slice.
    for stamp in stamps:
        ms = round(stamp * 1000)
        rows.extend([[MAGIC, ms >> 32, ms & 0xFFFFFFFF, 10000], [ident, 32300000, -110800000, 123]])
    return np.array(rows, dtype=np.int64).astype("<i4").tobytes()


def trace(stamp, times, ident="a00001"):
    return {
        "icao": ident,
        "timestamp": stamp,
        "trace": [
            [t, 32.3 + i * 0.0001, -110.8, 1234, 100, 0, 0, 0, None, "adsb_icao", 5000]
            for i, t in enumerate(times)
        ],
    }


def test_replay_parser_ignores_prefix_and_non_icao_and_rejects_wrong_day():
    start = epoch("2026-11-03T23:30:00")
    raw = heatmap([start, start + 10])
    ids, info = replay_candidates(
        gzip.compress(raw), start, start + 20, [32.2, -110.9, 32.4, -110.7], start
    )
    assert ids == {"a00001"} and info["slices"] == 2
    ids, info = replay_candidates(
        heatmap([start], 0x1A00001), start, start + 20, [32.2, -110.9, 32.4, -110.7], start
    )
    assert not ids and info["excluded_non_icao_points"] == 1
    with pytest.raises(ValueError, match="timestamp"):
        replay_candidates(raw, start, start + 20, [32.2, -110.9, 32.4, -110.7], start + 86400)
    with pytest.raises(ValueError, match="budget"):
        decode_body(gzip.compress(b"x" * 1000), 100)


def test_cross_midnight_fallback_does_not_duplicate_historical_date(tmp_path, monkeypatch):
    day = epoch("2026-11-03T00:00:00")
    nextday = day + 86400
    calls = Counter()

    def fetch(self, url, name, limit):
        calls[url] += 1
        if "heatmap/47" in url:
            return heatmap([nextday - 30, nextday - 20, nextday - 10])
        if "heatmap/00" in url:
            return heatmap([nextday, nextday + 10, nextday + 20])
        if "2026/11/03/traces" in url:
            return json.dumps(trace(day, [86360, 86370, 86380, 86390])).encode()
        if "2026/11/04/traces" in url:
            return None
        if "/data/traces/" in url:
            # Overlaps previous day; adapter must keep only the missing date's rows.
            return json.dumps(
                trace(day, [86360, 86370, 86380, 86390, 86400, 86410, 86420, 86430])
            ).encode()
        raise AssertionError(url)

    monkeypatch.setattr(WindowFetcher, "fetch", fetch)
    monkeypatch.setattr("doppler_lab.replay.time.time", lambda: nextday + 3600)
    result = download_window(
        "2026-11-03T23:59:10Z",
        "2026-11-04T00:00:40Z",
        [32.2, -110.9, 32.4, -110.7],
        tmp_path / "out",
        padding_s=0,
        max_gap_s=20,
    )
    assert result["status"] == "complete"
    assert result["normalization"]["exported_points"] == 8
    assert result["normalization"]["counts"].get("duplicate_fix", 0) == 0
    assert len(result["traces"]) == 2
    assert sum(v for k, v in calls.items() if "/data/traces/" in k) == 1


def test_rate_limit_stops_without_retry(tmp_path, monkeypatch):
    calls = []

    def fail(url):
        calls.append(url)
        raise urllib.error.HTTPError(url, 429, "rate limit", {}, None)

    monkeypatch.setattr("doppler_lab.replay.open_url", fail)
    with pytest.raises(ValueError, match="429"):
        download_window(
            "2026-11-03T23:20:00Z",
            "2026-11-03T23:25:00Z",
            [32.2, -110.9, 32.4, -110.7],
            tmp_path / "out",
        )
    assert len(calls) == 1
    assert json.loads((tmp_path / "out/download.json").read_text())["status"] == "failed"


def test_conflicts_quarantine_whole_aircraft_and_keep_alternatives(tmp_path):
    start = epoch("2026-11-03T23:00:00")
    bad = trace(start, [0, 5, 10, 15])
    bad["trace"].append([5, 32.33, -110.8, 1234, 100, 0, 0, 0, None, "adsb_icao", 5000])
    good = trace(start, [0, 5, 10, 15], "a00002")
    paths = []
    for data in (bad, good):
        p = tmp_path / (data["icao"] + ".json")
        p.write_text(json.dumps(data))
        paths.append(p)
    args = (
        paths,
        tmp_path / "out",
        "readsb-trace",
        "2026-11-03T23:00:00Z",
        "2026-11-03T23:01:00Z",
        [32.2, -110.9, 32.4, -110.7],
    )
    with pytest.raises(ValueError, match="Conflicting"):
        normalize(*args)
    result = normalize(*args, conflicts="quarantine")
    assert result["exported_points"] == 4
    assert result["quarantined_aircraft"][0]["icao"] == "a00001"
    assert result["counts"]["quarantined_points"] == 5
    assert result["segments"][0]["track_id"].startswith("a00002")
