from __future__ import annotations

import numpy as np
from shapely.geometry import LineString, Polygon

from .propagation import uma_los_probability, uma_pathloss_db


def dbm_to_mw(x):
    return 10.0 ** (np.asarray(x) / 10.0)


def mw_to_dbm(x):
    return 10.0 * np.log10(np.maximum(np.asarray(x), 1e-30))


def simulate_radio(grid_xy, site_xy, blockage_polys_xy, airport_mask, cfg):
    rng = np.random.default_rng(cfg.RANDOM_SEED)
    n_p = len(grid_xy)
    n_s = len(site_xy)

    dx = grid_xy[:, None, 0] - site_xy[None, :, 0]
    dy = grid_xy[:, None, 1] - site_xy[None, :, 1]
    d2d = np.sqrt(dx * dx + dy * dy)

    p_los = uma_los_probability(d2d, cfg.H_UT_M)
    if cfg.USE_AIRPORT_OPEN_AREA_HEURISTIC:
        p_los[airport_mask, :] = np.maximum(p_los[airport_mask, :], 0.90)

    los = rng.random((n_p, n_s)) < p_los
    pl = uma_pathloss_db(d2d, cfg.FC_GHZ, cfg.H_BS_M, cfg.H_UT_M, los)

    # Log-normal shadow fading. 3GPP UMa typical sigma values: 4 dB LOS, 6 dB NLOS.
    sigma = np.where(los, 4.0, 6.0)
    shadow = rng.normal(0.0, 1.0, size=(n_p, n_s)) * sigma
    pl = pl + shadow

    # Optional user-drawn blockage polygons from KML.
    blocked = np.zeros((n_p, n_s), dtype=bool)
    if blockage_polys_xy:
        # Grid sizes in this project are modest; explicit geometry is clear and robust.
        for i, p in enumerate(grid_xy):
            for j, s in enumerate(site_xy):
                link = LineString([tuple(s), tuple(p)])
                if any(link.crosses(poly) or link.within(poly) or link.intersects(poly) for poly in blockage_polys_xy):
                    blocked[i, j] = True
        pl = pl + blocked * cfg.BLOCKAGE_EXTRA_LOSS_DB

    # Convert total EIRP into an RSRP-like per-RE quantity.
    re_count = 12.0 * cfg.N_RB
    per_re_offset = 10.0 * np.log10(re_count)
    raw_rsrp = (
        cfg.EIRP_DBM + cfg.UE_GAIN_DBI - cfg.SYSTEM_LOSS_DB - pl - per_re_offset
    )

    # Initial serving cell from strongest un-beamformed pilot level.
    serving = np.argmax(raw_rsrp, axis=1)

    # Massive-MIMO abstraction: serving beam gets gain; non-serving leakage is suppressed.
    rsrp_eff = raw_rsrp - cfg.INTERFERENCE_REJECTION_DB
    rows = np.arange(n_p)
    rsrp_eff[rows, serving] = raw_rsrp[rows, serving] + cfg.MIMO_SERVING_GAIN_DB
    signal_dbm = rsrp_eff[rows, serving]

    total_mw = dbm_to_mw(rsrp_eff).sum(axis=1)
    sig_mw = dbm_to_mw(signal_dbm)
    interf_mw = np.maximum(total_mw - sig_mw, 0.0)

    # Noise per subcarrier-sized RE bandwidth.
    noise_dbm = -174.0 + 10.0 * np.log10(cfg.SCS_KHZ * 1e3) + cfg.NOISE_FIGURE_DB
    noise_mw = dbm_to_mw(noise_dbm)
    sinr_lin = sig_mw / (interf_mw + noise_mw)
    sinr_db = 10.0 * np.log10(np.maximum(sinr_lin, 1e-12))

    spectral_eff = np.minimum(np.log2(1.0 + sinr_lin), cfg.SPECTRAL_EFFICIENCY_CAP)
    throughput_mbps = cfg.BANDWIDTH_MHZ * cfg.IMPLEMENTATION_EFFICIENCY * spectral_eff

    # Number of cells with useful pilot level, used as an overlap indicator.
    overlap_count = (raw_rsrp >= cfg.RSRP_FAIR_DBM).sum(axis=1)

    return {
        "distance_m": d2d,
        "los": los,
        "blocked": blocked,
        "pathloss_db": pl,
        "raw_rsrp_dbm": raw_rsrp,
        "effective_rsrp_dbm": rsrp_eff,
        "serving": serving,
        "rsrp_dbm": signal_dbm,
        "sinr_db": sinr_db,
        "throughput_mbps": throughput_mbps,
        "overlap_count": overlap_count,
        "noise_dbm": noise_dbm,
    }
