from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


def recommend_weak_hotspot(grid_xy, weak_mask, site_xy, demand_weight):
    """Return a simple candidate new-site point in a weak, high-demand region.

    The score prefers weak points that are far from existing sites and have higher
    demand weight. This is a planning hint, not an automatic final site solution.
    """
    pts = grid_xy[weak_mask]
    if len(pts) == 0:
        return None
    tree = cKDTree(site_xy)
    d, _ = tree.query(pts, k=1)
    weights = demand_weight[weak_mask]
    score = d * weights
    idx = int(np.argmax(score))
    return pts[idx], float(d[idx]), float(score[idx])
