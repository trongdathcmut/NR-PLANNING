from __future__ import annotations

import numpy as np
from pyproj import CRS, Transformer
from shapely.geometry import Point, Polygon


def local_crs_from_lonlat(lon: float, lat: float) -> CRS:
    zone = int((lon + 180) // 6) + 1
    epsg = (32600 if lat >= 0 else 32700) + zone
    return CRS.from_epsg(epsg)


def transformers(boundary_lonlat):
    arr = np.asarray(boundary_lonlat, dtype=float)
    lon0, lat0 = arr[:, 0].mean(), arr[:, 1].mean()
    local = local_crs_from_lonlat(lon0, lat0)
    fwd = Transformer.from_crs("EPSG:4326", local, always_xy=True)
    inv = Transformer.from_crs(local, "EPSG:4326", always_xy=True)
    return fwd, inv, local


def project_lonlat(points_lonlat, fwd):
    arr = np.asarray(points_lonlat, dtype=float)
    x, y = fwd.transform(arr[:, 0], arr[:, 1])
    return np.column_stack([x, y])


def make_grid(boundary_xy: np.ndarray, step_m: float):
    poly = Polygon(boundary_xy)
    minx, miny, maxx, maxy = poly.bounds
    xs = np.arange(minx, maxx + step_m, step_m)
    ys = np.arange(miny, maxy + step_m, step_m)
    xx, yy = np.meshgrid(xs, ys)
    flat = np.column_stack([xx.ravel(), yy.ravel()])
    mask = np.array([poly.covers(Point(x, y)) for x, y in flat], dtype=bool)
    return flat[mask], xx, yy, mask.reshape(xx.shape), poly


def principal_airport_ellipse_mask(points_xy: np.ndarray, boundary_xy: np.ndarray):
    """Heuristic: central elongated ellipse = open airport/runway zone.

    This is NOT building data. It only creates a transparent, optional distinction
    between the central open airport and the denser urban ring.
    """
    b = np.asarray(boundary_xy)
    c = b.mean(axis=0)
    centered = b - c
    cov = np.cov(centered.T)
    vals, vecs = np.linalg.eigh(cov)
    order = np.argsort(vals)[::-1]
    vecs = vecs[:, order]
    rot_b = centered @ vecs
    ext = np.percentile(np.abs(rot_b), 95, axis=0)
    # Slightly conservative airport core; urban ring remains outside.
    a = max(ext[0] * 0.66, 1.0)
    bsemi = max(ext[1] * 0.50, 1.0)
    rot_p = (points_xy - c) @ vecs
    score = (rot_p[:, 0] / a) ** 2 + (rot_p[:, 1] / bsemi) ** 2
    return score <= 1.0, (c, vecs, a, bsemi)


def nearest_neighbor_distances(site_xy: np.ndarray) -> np.ndarray:
    d = np.sqrt(((site_xy[:, None, :] - site_xy[None, :, :]) ** 2).sum(axis=2))
    d[d == 0] = np.inf
    return d.min(axis=1)
