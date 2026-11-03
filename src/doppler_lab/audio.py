"""Local PCM audio and explicit short-time Fourier measurements."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import ShortTimeFFT, get_window, resample_poly


def read_audio(path, channel=0, target_rate=4000, max_seconds=1800):
    fs, raw = wavfile.read(path)
    if raw.ndim not in (1, 2) or len(raw) / fs > max_seconds:
        raise ValueError(f"Use mono/stereo WAV of at most {max_seconds} seconds; trim first.")
    channels = 1 if raw.ndim == 1 else raw.shape[1]
    if channel < 0 or channel >= channels:
        raise ValueError(f"Channel {channel} unavailable; this file has {channels} channel(s).")
    data = raw if raw.ndim == 1 else raw[:, channel]
    if raw.dtype == np.uint8:
        data = (data.astype(float) - 128) / 128
    elif np.issubdtype(raw.dtype, np.signedinteger):
        data = data.astype(float) / (float(np.iinfo(raw.dtype).max) + 1)
    elif np.issubdtype(raw.dtype, np.floating):
        data = data.astype(float)
    else:
        raise ValueError("Unsupported WAV sample format.")
    if len(data) == 0 or not np.isfinite(data).all():
        raise ValueError("Audio must have finite, nonempty samples.")
    if fs < target_rate:
        raise ValueError(f"Sample rate must be at least {target_rate} Hz.")
    peak = float(np.max(np.abs(data)))
    clip_fraction = float(np.mean(np.abs(data) >= 0.999))
    if fs != target_rate:
        divisor = int(np.gcd(fs, target_rate))
        data = resample_poly(data, target_rate // divisor, fs // divisor)
    return (
        target_rate,
        data,
        {
            "source_sample_rate_hz": int(fs),
            "channel": channel,
            "duration_s": len(raw) / fs,
            "peak": peak,
            "clipped_sample_fraction": clip_fraction,
        },
    )


@dataclass
class Spectrogram:
    times: np.ndarray
    frequencies: np.ndarray
    db: np.ndarray
    whitened: np.ndarray
    window_s: float
    hop_s: float


def spectrogram(audio, fs, window_s=2.0, hop_s=0.25, max_hz=600.0):
    if not 0 < hop_s <= window_s or not 20 <= max_hz < fs / 2:
        raise ValueError("Require 0 < hop <= window and 20 <= max_hz < Nyquist.")
    n, hop = round(window_s * fs), round(hop_s * fs)
    if n < 16 or hop < 1 or len(audio) < n:
        raise ValueError("Recording is shorter than the FFT window, or window/hop too small.")
    fft = ShortTimeFFT(get_window("hann", n), hop, fs, scale_to="psd")
    power = fft.spectrogram(np.asarray(audio, dtype=float))
    times = fft.t(len(audio))
    # Exclude zero-padded edge frames: absence of samples is not silence.
    keep_t = (times >= n / (2 * fs)) & (times <= (len(audio) - n / 2) / fs)
    keep_f = (fft.f >= 10) & (fft.f <= max_hz)
    db = 10 * np.log10(np.maximum(power[np.ix_(keep_f, keep_t)], 1e-20))
    whitened = db - np.median(db, axis=1, keepdims=True)
    return Spectrogram(times[keep_t], fft.f[keep_f], db, whitened, n / fs, hop / fs)


def line_scores(spec, frame_indices, ratios, source_hz):
    """Mean local line contrast (dB), not a likelihood or a probability.

    Compare the predicted line to flanks 6 Hz above/below; temporal median
    subtraction suppresses persistent hum. Core tolerance is +/-0.5 Hz.
    Every trial uses exactly the same frames and must be fully supported.
    """
    ratios = np.asarray(ratios)
    centers = np.asarray(source_hz)[:, None] * ratios[None, :]
    valid = (
        np.isfinite(centers).all(axis=1)
        & (np.min(centers, axis=1) >= spec.frequencies[0] + 6.5)
        & (np.max(centers, axis=1) <= spec.frequencies[-1] - 6.5)
    )
    scores = np.full(len(source_hz), -np.inf)
    if not valid.any():
        return scores
    centers = centers[valid]
    data = spec.whitened[:, frame_indices]
    bins = np.arange(len(frame_indices))[None, :]
    df = spec.frequencies[1] - spec.frequencies[0]

    def sample(offset):
        fractional = (centers + offset - spec.frequencies[0]) / df
        lo = np.floor(fractional).astype(int)
        weight = fractional - lo
        return data[lo, bins] * (1 - weight) + data[lo + 1, bins] * weight

    # Average rather than maximize the core: a max would reward noise fluctuations.
    core = (sample(-0.5) + sample(0) + sample(0.5)) / 3
    flank = (sample(-6) + sample(6)) / 2
    scores[valid] = np.mean(np.clip(core - flank, -30, 30), axis=1)
    return scores


def write_wav(path, fs, audio):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(path, fs, np.asarray(np.clip(audio, -1, 1) * 32767, dtype=np.int16))
