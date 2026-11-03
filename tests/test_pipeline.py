import json
from dataclasses import replace

import numpy as np
import pytest

from doppler_lab.case import load_case, local_path
from doppler_lab.importers import parse_utc
from doppler_lab.measure import fit_ridge
from doppler_lab.physics import straight_flyby
from doppler_lab.report import write_report
from doppler_lab.search import search
from doppler_lab.synthetic import create_case


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    folder = tmp_path_factory.mktemp("fixture") / "case"
    path = create_case(folder)
    return path


def small_case(path):
    case = load_case(path)
    return replace(
        case,
        observers=np.array([[100, -200, 0], [-600, 600, 0], [600, 600, 0]]),
        offsets=np.array([10.25, 11.25, 12.25]),
    )


def test_independent_waveform_recovers_nearby_location_without_truth(generated, tmp_path):
    case = small_case(generated)
    result, spec, ix = search(case)
    top = result["rows"][0]
    assert top["east_m"] == 100 and top["north_m"] == -200
    assert [e["track_id"] for e in top["events"]] == ["A", "B"]
    assert top["clock_offset_s"] == 11.25
    assert min(e["contrast_db"] for e in top["events"]) > 8
    assert result["accepted_location"] is False
    report = write_report(case, result, spec, ix, tmp_path / "report")
    assert "data:image/png;base64," in report.read_text(encoding="utf-8")
    data = json.loads((report.parent / "results.json").read_text())
    assert data["input_sha256"]["audio"] == case.hashes["audio"]


def test_shared_clock_does_not_independently_move_events(generated):
    case = small_case(generated)
    # Move only the second track's times. One common clock cannot repair both events.
    from doppler_lab.physics import Track

    tracks = dict(case.tracks)
    for name in ("B", "B-decoy"):
        old = tracks[name]
        tracks[name] = Track(name, old.times + 18, old.positions, old.max_gap_s)
    bad, _, _ = search(replace(case, tracks=tracks))
    good, _, _ = search(case)
    assert bad["rows"][0]["score_db"] < good["rows"][0]["score_db"] - 3


def test_noise_control_does_not_pass_signal_heuristic(tmp_path):
    case = small_case(create_case(tmp_path / "noise", noise_only=True))
    result, _, _ = search(case)
    assert result["rows"][0]["score_db"] < 3
    assert result["accepted_location"] is False


def test_case_escape_and_naive_clock_rejected(tmp_path):
    with pytest.raises(ValueError, match="inside"):
        local_path(tmp_path, "../secret.wav")
    with pytest.raises(ValueError, match="UTC"):
        parse_utc("2026-11-03T12:00:00")
    assert parse_utc("2026-11-03T12:00:00Z") == parse_utc("2026-11-03T05:00:00-07:00")


def test_manually_traced_ideal_ridge_fit(tmp_path):
    t = np.linspace(-60, 70, 80)
    f = straight_flyby(t, 92, 1800, 0, 135)
    path = tmp_path / "ridge.csv"
    np.savetxt(
        path, np.column_stack((t, f)), delimiter=",", header="time_s,frequency_hz", comments=""
    )
    result = fit_ridge(path)
    assert result["speed_m_s"] == pytest.approx(92, rel=0.001)
    assert result["cpa_slant_m"] == pytest.approx(1800, rel=0.001)
    assert result["residual_rmse_hz"] < 0.001
