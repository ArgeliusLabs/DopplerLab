import copy
import json
from dataclasses import replace

import numpy as np
import pytest

from doppler_lab.case import axis_values, load_case
from doppler_lab.cli import main
from doppler_lab.importers import import_tracks
from doppler_lab.physics import Track
from doppler_lab.search import search
from doppler_lab.synthetic import create_case


def test_single_straight_flyover_has_mirror_ambiguity():
    t = np.arange(-80, 81, 1.0)
    track = Track("linear", t, np.column_stack((90 * t, t * 0, t * 0 + 1300))).sample()
    arrival = np.linspace(-50, 50, 100)
    np.testing.assert_allclose(
        track.predict([0, 500, 0], arrival), track.predict([0, -500, 0], arrival), atol=1e-12
    )


def test_translation_does_not_change_the_acoustics():
    t = np.arange(30.0)
    xyz = np.column_stack((90 * t, t * 0 + 500, t * 0 + 1000))
    shift = np.array([1234, -4321, 50])
    before = Track("first", t, xyz).sample()
    after = Track("second", t, xyz + shift).sample()
    np.testing.assert_allclose(
        before.predict([10, 20, 0], [10, 15, 20]),
        after.predict(np.array([10, 20, 0]) + shift, [10, 15, 20]),
    )


@pytest.mark.parametrize("axis", [[0, 1, 0], [2, 1, 1], [0, float("inf"), 1]])
def test_invalid_grid_axes_are_rejected(axis):
    with pytest.raises(ValueError):
        axis_values(axis, "test")


def test_real_track_import_has_explicit_epoch_and_compatible_height(tmp_path):
    source = tmp_path / "geo.csv"
    source.write_text(
        "track_id,timestamp_utc,latitude_deg,longitude_deg,height_ellipsoid_m\n"
        "A,2026-11-03T20:00:02Z,33,-112,500\n",
        encoding="utf-8",
    )
    output = tmp_path / "local.csv"
    assert import_tracks(source, output, [33, -112, 400], "2026-11-03T20:00:00Z") == 1
    values = output.read_text().splitlines()[1].split(",")
    np.testing.assert_allclose([float(v) for v in values[1:]], [2, 0, 0, 100], atol=1e-5)
    with pytest.raises(ValueError, match="already exists"):
        import_tracks(source, output, [33, -112, 400], "2026-11-03T20:00:00Z")


def test_case_rejects_duplicate_event_harmonics_and_unsupported_window(tmp_path):
    path = create_case(tmp_path / "case", noise_only=True)
    base = json.loads(path.read_text())
    bad = copy.deepcopy(base)
    bad["events"][1]["start_s"] = 30
    (path.parent / "overlap.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="overlap"):
        load_case(path.parent / "overlap.json")
    case = load_case(path)
    case = replace(case, observers=np.array([[0, 0, 0]]), offsets=np.array([1000.0]))
    result, _, _ = search(case)
    assert result["status"] == "no_supported_candidate"
    assert not result["rows"]
    assert result["unsupported_line_trials"] == result["line_trials_evaluated"]


def test_cli_invalid_inputs_exit_cleanly(tmp_path, capsys):
    assert main(["demo", "--output", str(tmp_path / "bad"), "--source-drift-hz", "nan"]) == 2
    assert "Error:" in capsys.readouterr().err
