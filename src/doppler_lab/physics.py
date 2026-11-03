"""Stationary receiver, subsonic source, homogeneous still air; all SI units.

Range rate is positive when receding. Arrival time is t_emit + range/c,
and observed frequency is f_source / (1 + range_rate/c).
"""

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import PchipInterpolator


def sound_speed(temperature_c: float) -> float:
    """Dry-air approximation, not an atmospheric propagation model."""
    if not np.isfinite(temperature_c) or not -50 <= temperature_c <= 60:
        raise ValueError("Temperature must be finite and between -50 and 60 C.")
    return 331.3 * np.sqrt(1 + temperature_c / 273.15)


@dataclass
class Track:
    name: str
    times: np.ndarray
    positions: np.ndarray
    max_gap_s: float = 5.0

    def __post_init__(self):
        self.times = np.asarray(self.times, dtype=float)
        self.positions = np.asarray(self.positions, dtype=float)
        if self.times.ndim != 1 or len(self.times) < 4:
            raise ValueError(f"Track {self.name}: need at least four timestamps.")
        if self.positions.shape != (len(self.times), 3):
            raise ValueError(f"Track {self.name}: expected N x 3 coordinates.")
        if not np.isfinite(self.times).all() or not np.isfinite(self.positions).all():
            raise ValueError(f"Track {self.name}: nonfinite samples.")
        gaps = np.diff(self.times)
        if np.any(gaps <= 0):
            raise ValueError(f"Track {self.name}: timestamps must be strictly increasing.")
        if self.max_gap_s <= 0 or np.any(gaps > self.max_gap_s):
            raise ValueError(f"Track {self.name}: gap exceeds max_gap_s; split the track.")
        self.interpolator = PchipInterpolator(self.times, self.positions, axis=0)

    def sample(self, step_s=0.25):
        if not np.isfinite(step_s) or step_s <= 0:
            raise ValueError("Model sampling interval must be positive.")
        n = int(np.ceil((self.times[-1] - self.times[0]) / step_s)) + 1
        if n > 200_000:
            raise ValueError("Track is too long for this local solver; trim it first.")
        t = np.linspace(self.times[0], self.times[-1], n)
        return SampledTrack(self.name, t, self.interpolator(t), self.interpolator(t, 1))


@dataclass
class SampledTrack:
    name: str
    times: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray

    def propagation(self, observer, c=343.0):
        observer = np.asarray(observer, dtype=float)
        if observer.shape != (3,) or not np.isfinite(observer).all():
            raise ValueError("Observer must have three finite coordinates.")
        if not np.isfinite(c) or c <= 0:
            raise ValueError("Sound speed must be positive.")
        if np.any(np.linalg.norm(self.velocities, axis=1) >= 0.9 * c):
            raise ValueError(f"Track {self.name}: unsupported speed >= 0.9 Mach.")
        delta = self.positions - observer
        ranges = np.linalg.norm(delta, axis=1)
        if np.any(ranges < 1):
            raise ValueError("A candidate lies within 1 m of an aircraft track.")
        range_rate = np.sum(delta * self.velocities, axis=1) / ranges
        arrival = self.times + ranges / c
        if np.any(np.diff(arrival) <= 0):
            raise ValueError("Non-monotonic arrival time; propagation is unsupported.")
        ratio = 1 / (1 + range_rate / c)
        return arrival, ratio, ranges

    def predict(self, observer, arrival_times, c=343.0):
        arrival, ratio, _ = self.propagation(observer, c)
        return np.interp(arrival_times, arrival, ratio, left=np.nan, right=np.nan)


def straight_flyby(arrival_times, speed, slant_m, cpa_emission_s, f0_hz, c=343.0):
    """Analytic retarded-time inversion for a constant-speed straight flyby.

    cpa_emission_s is the geometric closest approach, not when it is heard.
    Solves c*(t_arrive-t_emit) = sqrt(v^2*(t_emit-t_cpa)^2 + d^2).
    """
    if not 0 < speed < 0.9 * c or slant_m <= 0 or f0_hz <= 0:
        raise ValueError("Require 0 < speed < 0.9 c, positive distance and frequency.")
    u = np.asarray(arrival_times, dtype=float) - cpa_emission_s
    denominator = c * c - speed * speed
    tau = (
        c * c * u - np.sqrt(c * c * speed * speed * u * u + denominator * slant_m * slant_m)
    ) / denominator
    radius = np.sqrt((speed * tau) ** 2 + slant_m**2)
    return f0_hz / (1 + speed * speed * tau / (radius * c))


def geodetic_to_ecef(lat_deg, lon_deg, height_m):
    """WGS84 ellipsoid height, never pressure altitude or an unconverted DEM."""
    lat, lon, h = np.broadcast_arrays(lat_deg, lon_deg, height_m)
    if not all(np.isfinite(x).all() for x in (lat, lon, h)):
        raise ValueError("Geodetic coordinates must be finite.")
    if np.any(np.abs(lat) > 90) or np.any(np.abs(lon) > 180):
        raise ValueError("Latitude/longitude out of range.")
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    a, e2 = 6378137.0, 6.6943799901413165e-3
    n = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    return np.stack(
        (
            (n + h) * np.cos(lat) * np.cos(lon),
            (n + h) * np.cos(lat) * np.sin(lon),
            (n * (1 - e2) + h) * np.sin(lat),
        ),
        axis=-1,
    )


def geodetic_to_enu(lat, lon, height, origin):
    xyz = geodetic_to_ecef(lat, lon, height) - geodetic_to_ecef(*origin)
    phi, lam = np.deg2rad(origin[:2])
    rotation = np.array(
        [
            [-np.sin(lam), np.cos(lam), 0],
            [-np.sin(phi) * np.cos(lam), -np.sin(phi) * np.sin(lam), np.cos(phi)],
            [np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)],
        ]
    )
    return xyz @ rotation.T
