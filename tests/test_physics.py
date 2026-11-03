import numpy as np
import pytest

from doppler_lab.physics import Track, geodetic_to_enu, sound_speed, straight_flyby


def test_retarded_curve_matches_independent_analytic_solution():
    t = np.arange(-100, 101, 1.0)
    v, d, c, f0 = 90.0, 1600.0, 343.0, 130.0
    track = Track("linear", t, np.column_stack((v * t, np.full_like(t, d), t * 0)))
    arrival = np.linspace(-60, 65, 400)
    predicted = f0 * track.sample(0.05).predict([0, 0, 0], arrival, c)
    expected = straight_flyby(arrival, v, d, 0, f0, c)
    np.testing.assert_allclose(predicted, expected, atol=0.0002)


def test_cpa_is_heard_later_and_approaching_has_higher_pitch():
    c, d, f0 = 343.0, 1500.0, 150.0
    output = straight_flyby(np.array([-60, d / c, 60]), 90, d, 0, f0, c)
    assert output[0] > f0 > output[2]
    assert output[1] == pytest.approx(f0)


def test_no_time_extrapolation():
    t = np.arange(10.0)
    track = Track("still", t, np.column_stack((0 * t, 0 * t + 1000, 0 * t))).sample()
    assert np.isnan(track.predict([0, 0, 0], [-100, 100])).all()


@pytest.mark.parametrize("times", [[0, 1, 1, 2], [0, 2, 1, 3], [0, 1, 2, 20]])
def test_bad_track_timing_is_rejected(times):
    with pytest.raises(ValueError):
        Track("bad", np.array(times), np.ones((4, 3)))


def test_supersonic_track_rejected():
    t = np.arange(10.0)
    track = Track("fast", t, np.column_stack((400 * t, 0 * t + 1000, 0 * t))).sample()
    with pytest.raises(ValueError, match="speed"):
        track.predict([0, 0, 0], [5])


def test_geographic_conversion_origin_and_vertical():
    origin = [33.0, -112.0, 400.0]
    np.testing.assert_allclose(geodetic_to_enu(33, -112, 400, origin), [0, 0, 0], atol=1e-8)
    np.testing.assert_allclose(geodetic_to_enu(33, -112, 500, origin), [0, 0, 100], atol=1e-6)
    east = geodetic_to_enu(33, -111.999, 400, origin)
    assert east[0] > 90 and abs(east[1]) < 0.01


def test_temperature():
    assert sound_speed(20) == pytest.approx(343.2, abs=0.2)
    with pytest.raises(ValueError):
        sound_speed(float("nan"))
