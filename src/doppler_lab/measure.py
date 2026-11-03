"""Fit a manually traced ridge to the ideal straight, constant-tone flyby model."""

import csv
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from .physics import straight_flyby


def fit_ridge(path, c=343.0):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) < 12:
        raise ValueError("Trace at least 12 samples spanning both sides of a flyover.")
    t = np.array([float(r["time_s"]) for r in rows])
    f = np.array([float(r["frequency_hz"]) for r in rows])
    if (
        not np.isfinite(t).all()
        or not np.isfinite(f).all()
        or np.any(f <= 0)
        or np.any(np.diff(t) <= 0)
        or np.ptp(t) < 10
    ):
        raise ValueError(
            "Ridge needs finite positive frequencies and increasing times spanning 10 s."
        )
    # Multiple starts reduce local-minimum dependence; estimates remain conditional.
    lower = [10, 100, t[0] - 120, min(f) * 0.6]
    upper = [min(250, 0.89 * c), 15000, t[-1], max(f) * 1.4]
    fits = []
    for v in (50, 100, 170):
        for d in (800, 3000, 7000):
            p0 = [v, d, float(np.median(t) - d / c), float(np.median(f))]
            p0 = np.clip(p0, np.array(lower) + 1e-6, np.array(upper) - 1e-6)
            fits.append(
                least_squares(
                    lambda p: straight_flyby(t, *p, c=c) - f,
                    p0,
                    bounds=(lower, upper),
                    loss="soft_l1",
                    x_scale="jac",
                    max_nfev=2000,
                )
            )
    best = min(fits, key=lambda fit: fit.cost)
    v, d, tcpa, f0 = best.x
    singular = np.linalg.svd(best.jac, compute_uv=False)
    condition = float(singular[0] / max(singular[-1], 1e-15))
    bound_fraction = (best.x - lower) / (np.array(upper) - lower)
    return {
        "speed_m_s": float(v),
        "cpa_slant_m": float(d),
        "cpa_emission_s": float(tcpa),
        "cpa_arrival_s": float(tcpa + d / c),
        "source_hz": float(f0),
        "residual_rmse_hz": float(np.sqrt(np.mean(best.fun**2))),
        "optimizer_success": bool(best.success),
        "jacobian_condition_number": condition,
        "near_bound": bool(np.any((bound_fraction < 0.01) | (bound_fraction > 0.99))),
        "warning": "Ideal-model estimates, not exact aircraft speed/distance. Source RPM drift, "
        "turns, partial curves and weather can invalidate them. Use broad bounds.",
    }
