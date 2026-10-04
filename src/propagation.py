from __future__ import annotations

import numpy as np

C = 299_792_458.0


def uma_los_probability(d2d_m: np.ndarray, h_ut_m: float = 1.5) -> np.ndarray:
    """3GPP TR 38.901 UMa LOS probability (base form for low-height UE)."""
    d = np.maximum(np.asarray(d2d_m, dtype=float), 1.0)
    p = np.minimum(18.0 / d, 1.0) * (1.0 - np.exp(-d / 63.0)) + np.exp(-d / 63.0)
    # Height correction is zero for the default 1.5 m UE; keep the base form transparent.
    return np.clip(p, 0.0, 1.0)


def uma_pathloss_db(
    d2d_m: np.ndarray,
    fc_ghz: float,
    h_bs_m: float,
    h_ut_m: float,
    is_los: np.ndarray,
) -> np.ndarray:
    """3GPP TR 38.901 Urban Macro LOS/NLOS path loss, educational implementation."""
    d2d = np.clip(np.asarray(d2d_m, dtype=float), 10.0, 5000.0)
    d3d = np.sqrt(d2d**2 + (h_bs_m - h_ut_m) ** 2)

    h_bs_eff = max(h_bs_m - 1.0, 1.0)
    h_ut_eff = max(h_ut_m - 1.0, 0.5)
    d_bp = 4.0 * h_bs_eff * h_ut_eff * (fc_ghz * 1e9) / C

    pl1 = 28.0 + 22.0 * np.log10(d3d) + 20.0 * np.log10(fc_ghz)
    pl2 = (
        28.0
        + 40.0 * np.log10(d3d)
        + 20.0 * np.log10(fc_ghz)
        - 9.0 * np.log10(d_bp**2 + (h_bs_m - h_ut_m) ** 2)
    )
    pl_los = np.where(d2d <= d_bp, pl1, pl2)

    pl_nlos_prime = (
        13.54
        + 39.08 * np.log10(d3d)
        + 20.0 * np.log10(fc_ghz)
        - 0.6 * (h_ut_m - 1.5)
    )
    pl_nlos = np.maximum(pl_los, pl_nlos_prime)
    return np.where(is_los, pl_los, pl_nlos)
