import numpy as np
import pytest
from scipy.io import wavfile

from doppler_lab.audio import line_scores, read_audio, spectrogram


def test_antiphase_stereo_keeps_selected_channel(tmp_path):
    fs = 8000
    wave = 0.5 * np.sin(2 * np.pi * 130 * np.arange(fs * 3) / fs)
    path = tmp_path / "stereo.wav"
    wavfile.write(path, fs, np.column_stack((wave, -wave)).astype(np.float32))
    _, left, _ = read_audio(path, 0)
    _, right, _ = read_audio(path, 1)
    assert np.std(left) > 0.3
    np.testing.assert_allclose(left, -right)
    with pytest.raises(ValueError):
        read_audio(path, 2)


def test_stationary_hum_is_not_a_doppler_match():
    fs = 4000
    audio = 0.3 * np.sin(2 * np.pi * 130 * np.arange(fs * 20) / fs)
    spec = spectrogram(audio, fs)
    ix = np.arange(len(spec.times))
    score = line_scores(spec, ix, np.ones(len(ix)), [130])[0]
    assert abs(score) < 0.1


def test_out_of_band_prediction_not_clipped_into_valid_bins():
    spec = spectrogram(np.zeros(4000 * 10), 4000)
    ix = np.arange(len(spec.times))
    assert np.isneginf(line_scores(spec, ix, np.ones(len(ix)), [4, 700])).all()


def test_fft_time_frequency_axes_and_full_windows():
    fs = 4000
    spec = spectrogram(np.zeros(fs * 10), fs, 2, 0.25, 600)
    assert spec.times[0] == 1
    assert spec.times[-1] == 9
    assert spec.frequencies[1] - spec.frequencies[0] == 0.5
