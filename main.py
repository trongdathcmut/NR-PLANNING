from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

import config as cfg
from src.kml_io import read_project
from src.geo import transformers, project_lonlat, make_grid, principal_airport_ellipse_mask, nearest_neighbor_distances
from src.radio import simulate_radio
from src.optimizer import recommend_weak_hotspot
from src.viz import plot_scalar, plot_serving, plot_layout, plot_cdf, write_interactive_map


ROOT = Path(__file__).resolve().parent
DEFAULT_KML = ROOT / "data" / "full_gnb.kml"
RESULTS = ROOT / "results"


def pct(mask, weights=None):
    mask = np.asarray(mask, dtype=float)
    if weights is None:
        return float(mask.mean() * 100.0)
    w = np.asarray(weights, dtype=float)
    return float((mask * w).sum() / w.sum() * 100.0)


def main(kml_path: str | Path = DEFAULT_KML):
    RESULTS.mkdir(exist_ok=True)
    project = read_project(kml_path)
    fwd, inv, local_crs = transformers(project.boundary_lonlat)
    boundary_xy = project_lonlat(project.boundary_lonlat, fwd)
    site_xy = project_lonlat([(s.lon, s.lat) for s in project.sites], fwd)

    grid_xy, xx, yy, grid_mask, boundary_poly = make_grid(boundary_xy, cfg.GRID_STEP_M)
    airport_mask, ellipse_meta = principal_airport_ellipse_mask(grid_xy, boundary_xy)
    if not cfg.USE_AIRPORT_OPEN_AREA_HEURISTIC:
        airport_mask[:] = False

    blockage_polys_xy = []
    for _, lonlat in project.blockages:
        blockage_polys_xy.append(Polygon(project_lonlat(lonlat, fwd)))

    radio = simulate_radio(grid_xy, site_xy, blockage_polys_xy, airport_mask, cfg)
    serving = radio["serving"]
    rsrp = radio["rsrp_dbm"]
    sinr = radio["sinr_db"]
    tp = radio["throughput_mbps"]
    overlap = radio["overlap_count"]

    demand = np.where(airport_mask, cfg.AIRPORT_DEMAND_WEIGHT, cfg.URBAN_DEMAND_WEIGHT)
    weak = (rsrp < cfg.WEAK_RSRP_DBM) | (sinr < cfg.WEAK_SINR_DB)
    candidate = recommend_weak_hotspot(grid_xy, weak, site_xy, demand)
    candidate_lonlat = None
    if candidate is not None:
        (cx, cy), dist_m, score = candidate
        clon, clat = inv.transform(cx, cy)
        candidate_lonlat = (clon, clat)

    cell_area_km2 = (cfg.GRID_STEP_M**2) / 1e6
    nearest = nearest_neighbor_distances(site_xy) / 1000.0
    site_rows = []
    for i, s in enumerate(project.sites):
        m = serving == i
        if m.any():
            site_rows.append({
                "site": s.name,
                "latitude": s.lat,
                "longitude": s.lon,
                "nearest_neighbor_km": nearest[i],
                "served_area_km2": m.sum() * cell_area_km2,
                "served_points": int(m.sum()),
                "median_rsrp_dbm": float(np.median(rsrp[m])),
                "p10_rsrp_dbm": float(np.percentile(rsrp[m], 10)),
                "median_sinr_db": float(np.median(sinr[m])),
                "avg_throughput_mbps": float(np.mean(tp[m])),
                "weak_fraction_pct": float(weak[m].mean() * 100),
            })
        else:
            site_rows.append({
                "site": s.name, "latitude": s.lat, "longitude": s.lon,
                "nearest_neighbor_km": nearest[i], "served_area_km2": 0.0,
                "served_points": 0, "median_rsrp_dbm": np.nan, "p10_rsrp_dbm": np.nan,
                "median_sinr_db": np.nan, "avg_throughput_mbps": np.nan,
                "weak_fraction_pct": 100.0,
            })
    site_stats = pd.DataFrame(site_rows)
    site_stats.to_csv(RESULTS / "site_kpis.csv", index=False)

    lon, lat = inv.transform(grid_xy[:, 0], grid_xy[:, 1])
    grid_df = pd.DataFrame({
        "longitude": lon,
        "latitude": lat,
        "serving_site": [project.sites[i].name for i in serving],
        "rsrp_dbm": rsrp,
        "sinr_db": sinr,
        "throughput_mbps": tp,
        "overlap_cells": overlap,
        "airport_open_heuristic": airport_mask,
        "demand_weight": demand,
        "weak": weak,
    })
    grid_df.to_csv(RESULTS / "grid_results.csv", index=False)

    network_kpis = {
        "study_area_km2": len(grid_xy) * cell_area_km2,
        "site_count": len(project.sites),
        "median_nearest_neighbor_km": float(np.median(nearest)),
        "coverage_rsrp_ge_-105_pct": pct(rsrp >= cfg.RSRP_FAIR_DBM, demand),
        "coverage_rsrp_ge_-95_pct": pct(rsrp >= cfg.RSRP_GOOD_DBM, demand),
        "sinr_ge_0_pct": pct(sinr >= cfg.SINR_USABLE_DB, demand),
        "sinr_ge_13_pct": pct(sinr >= cfg.SINR_GOOD_DB, demand),
        "weak_area_pct": pct(weak, demand),
        "median_rsrp_dbm": float(np.median(rsrp)),
        "median_sinr_db": float(np.median(sinr)),
        "median_throughput_mbps": float(np.median(tp)),
        "overlap_3plus_pct": pct(overlap >= 3, demand),
    }
    if candidate_lonlat:
        network_kpis["candidate_site_latitude"] = candidate_lonlat[1]
        network_kpis["candidate_site_longitude"] = candidate_lonlat[0]
        network_kpis["candidate_distance_to_nearest_site_m"] = candidate[1]
    pd.DataFrame([network_kpis]).to_csv(RESULTS / "network_kpis.csv", index=False)

    plot_layout(boundary_xy, site_xy, [s.name for s in project.sites], airport_mask, grid_xy, RESULTS / "01_layout.png")
    plot_scalar(grid_xy, rsrp, boundary_xy, site_xy, [s.name for s in project.sites], "RSRP-like coverage map", "RSRP (dBm)", RESULTS / "02_rsrp.png", -125, -70)
    plot_scalar(grid_xy, sinr, boundary_xy, site_xy, [s.name for s in project.sites], "SINR map", "SINR (dB)", RESULTS / "03_sinr.png", -10, 30)
    plot_serving(grid_xy, serving, boundary_xy, site_xy, [s.name for s in project.sites], RESULTS / "04_serving_cell.png")
    plot_scalar(grid_xy, tp, boundary_xy, site_xy, [s.name for s in project.sites], "Estimated downlink throughput map", "Throughput (Mbps)", RESULTS / "05_throughput.png", 0, min(600, np.percentile(tp, 99)))
    plot_scalar(grid_xy, overlap, boundary_xy, site_xy, [s.name for s in project.sites], "Coverage overlap map", "Cells above fair-RSRP threshold", RESULTS / "06_overlap.png", 0, max(4, int(overlap.max())))
    plot_cdf(rsrp, "RSRP (dBm)", "CDF of RSRP", RESULTS / "07_rsrp_cdf.png")
    plot_cdf(sinr, "SINR (dB)", "CDF of SINR", RESULTS / "08_sinr_cdf.png")

    write_interactive_map(project.boundary_lonlat, project.sites, site_stats, candidate_lonlat, RESULTS / "interactive_map.html")

    print("\n=== 5G NR PYTHON PLANNING ===")
    print(f"KML: {kml_path}")
    print(f"Local CRS: {local_crs.to_string()}")
    print(f"Sites: {len(project.sites)} | grid points: {len(grid_xy)}")
    for k, v in network_kpis.items():
        if isinstance(v, float):
            print(f"{k}: {v:.3f}")
        else:
            print(f"{k}: {v}")
    print("\nSite KPIs:")
    print(site_stats.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print(f"\nResults written to: {RESULTS}")


if __name__ == "__main__":
    kml = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_KML
    main(kml)
