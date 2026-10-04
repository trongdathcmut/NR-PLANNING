from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib.patches import Polygon as MplPolygon
import folium
from branca.colormap import LinearColormap


def _common(ax, boundary_xy, site_xy, site_names, title):
    ax.add_patch(MplPolygon(boundary_xy, closed=True, fill=False, linewidth=2.2))
    ax.scatter(site_xy[:, 0], site_xy[:, 1], marker="^", s=85, zorder=5)
    for (x, y), name in zip(site_xy, site_names):
        ax.annotate(name, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8, weight="bold")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Local Easting (m)")
    ax.set_ylabel("Local Northing (m)")
    ax.set_title(title)


def plot_scalar(grid_xy, values, boundary_xy, site_xy, site_names, title, label, out_path, vmin=None, vmax=None):
    fig, ax = plt.subplots(figsize=(9, 7))
    sc = ax.scatter(grid_xy[:, 0], grid_xy[:, 1], c=values, s=18, vmin=vmin, vmax=vmax)
    _common(ax, boundary_xy, site_xy, site_names, title)
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label(label)
    fig.tight_layout()
    fig.savefig(out_path, dpi=190)
    plt.close(fig)


def plot_serving(grid_xy, serving, boundary_xy, site_xy, site_names, out_path):
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(grid_xy[:, 0], grid_xy[:, 1], c=serving, s=18, cmap="tab10")
    _common(ax, boundary_xy, site_xy, site_names, "Serving-cell map")
    fig.tight_layout()
    fig.savefig(out_path, dpi=190)
    plt.close(fig)


def plot_layout(boundary_xy, site_xy, site_names, airport_mask_points, grid_xy, out_path):
    fig, ax = plt.subplots(figsize=(9, 7))
    if airport_mask_points is not None:
        ax.scatter(grid_xy[airport_mask_points, 0], grid_xy[airport_mask_points, 1], s=7, alpha=0.15, label="Airport/open-area heuristic")
    _common(ax, boundary_xy, site_xy, site_names, "5G NR initial planning layout from Google Earth KML")
    # nearest-neighbor links for visual sanity check
    for i in range(len(site_xy)):
        d = np.sqrt(((site_xy - site_xy[i]) ** 2).sum(axis=1))
        d[i] = np.inf
        j = int(np.argmin(d))
        ax.plot([site_xy[i, 0], site_xy[j, 0]], [site_xy[i, 1], site_xy[j, 1]], linestyle="--", linewidth=0.7)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=190)
    plt.close(fig)


def plot_cdf(values, xlabel, title, out_path):
    x = np.sort(np.asarray(values))
    y = np.arange(1, len(x) + 1) / len(x)
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.plot(x, y, linewidth=2)
    ax.grid(True, alpha=0.25)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("CDF")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=190)
    plt.close(fig)


def write_interactive_map(boundary_lonlat, sites, site_stats, candidate_lonlat, out_path):
    arr = np.asarray(boundary_lonlat)
    center = [arr[:, 1].mean(), arr[:, 0].mean()]
    m = folium.Map(location=center, zoom_start=14, tiles="OpenStreetMap")
    folium.Polygon(
        locations=[[lat, lon] for lon, lat in boundary_lonlat],
        tooltip="5G NR study area",
        fill=False,
        weight=3,
    ).add_to(m)

    stat_by_name = {r["site"]: r for _, r in site_stats.iterrows()}
    for s in sites:
        st = stat_by_name.get(s.name, {})
        html = (
            f"<b>{s.name}</b><br>Lat: {s.lat:.6f}<br>Lon: {s.lon:.6f}"
            f"<br>Served area: {float(st.get('served_area_km2', 0)):.2f} km²"
            f"<br>Median RSRP: {float(st.get('median_rsrp_dbm', 0)):.1f} dBm"
            f"<br>Median SINR: {float(st.get('median_sinr_db', 0)):.1f} dB"
        )
        folium.Marker([s.lat, s.lon], tooltip=s.name, popup=folium.Popup(html, max_width=320)).add_to(m)

    if candidate_lonlat is not None:
        lon, lat = candidate_lonlat
        folium.Marker(
            [lat, lon],
            tooltip="Candidate weak-zone site",
            popup="Planning hint: candidate point from weak-coverage scoring; verify feasibility in Google Earth.",
            icon=folium.Icon(color="red", icon="plus"),
        ).add_to(m)

    m.save(out_path)
