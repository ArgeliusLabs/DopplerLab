import json

import pytest

from doppler_lab.media import aware_time, timing_evidence, utc_days


def test_recording_claim_beats_export_time_without_copying_gps():
    probe = {
        "format": {
            "tags": {
                "com.apple.quicktime.creationdate": "2026-11-03T16:19:48-0700",
                "creation_time": "2026-11-04T00:24:18Z",
                "com.apple.quicktime.location.ISO6709": "+12.3456-078.9012/",
                "comment": "private note",
            }
        }
    }
    evidence = timing_evidence(probe)
    assert evidence["suggested_sample_zero_utc"] == "2026-11-03T23:19:48+00:00"
    assert evidence["location_metadata_present"]
    assert "+12.3456" not in json.dumps(evidence)
    assert "private note" not in json.dumps(evidence)
    assert utc_days(evidence["suggested_sample_zero_utc"], 2863.6) == ["2026-11-03", "2026-11-04"]


def test_container_date_alone_is_not_sample_zero_and_override_is_explicit():
    probe = {"format": {"tags": {"creation_time": "2026-11-04T00:24:18Z"}}}
    assert timing_evidence(probe)["suggested_sample_zero_utc"] is None
    override = timing_evidence(probe, "2026-11-03T17:00:00-07:00")
    assert override["basis"] == "analyst override"
    assert override["suggested_sample_zero_utc"] == "2026-11-04T00:00:00+00:00"
    with pytest.raises(ValueError, match="offset"):
        aware_time("2026-11-03T17:00:00")


def test_uncertainty_and_sound_delay_padding_include_previous_day():
    assert utc_days("2026-11-04T00:01:00Z", 60, 60, 180) == ["2026-11-03", "2026-11-04"]
