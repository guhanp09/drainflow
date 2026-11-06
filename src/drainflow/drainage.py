"""Minimax spill connectivity on a four-neighbor floor graph."""

import heapq

import numpy as np

from drainflow.geometry import floor_height, validate


def spill_surface(terrain, seeds):
    """Minimum escape barrier: min over paths of the maximum elevation along each path."""
    z = np.asarray(terrain, dtype=float)
    if z.ndim != 2 or not np.isfinite(z).all():
        raise ValueError("Finite 2D terrain required")
    spill = np.full(z.shape, np.inf)
    queue = []
    for row, col, level in seeds:
        h = max(float(level), float(z[row, col]))
        if h < spill[row, col]:
            spill[row, col] = h
            heapq.heappush(queue, (h, row, col))
    if not queue:
        raise ValueError("At least one outlet/rim seed is required")
    nr, nc = z.shape
    while queue:
        h, i, j = heapq.heappop(queue)
        if h > spill[i, j]:
            continue
        for a, b in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
            if 0 <= a < nr and 0 <= b < nc:
                candidate = max(h, z[a, b])
                if candidate < spill[a, b]:
                    spill[a, b] = candidate
                    heapq.heappush(queue, (candidate, a, b))
    return spill


def vertical_coordinates(x, y, z, length, width, longitudinal_deg, transverse_deg):
    if (
        not np.isfinite([longitudinal_deg, transverse_deg]).all()
        or max(abs(longitudinal_deg), abs(transverse_deg)) >= 45
    ):
        raise ValueError("Tilt must be finite and smaller than 45 degrees")
    a, b = np.radians([longitudinal_deg, transverse_deg])
    return (
        np.sin(a) * (x - length / 2)
        + np.cos(a) * np.sin(b) * (y - width / 2)
        + np.cos(a) * np.cos(b) * z
    )


def discharge(head_m, diameter_m, coefficient=0.62, gravity=9.80665):
    if (
        not np.isfinite([head_m, diameter_m, coefficient, gravity]).all()
        or diameter_m <= 0
        or not 0 < coefficient <= 1
        or gravity <= 0
    ):
        raise ValueError("Invalid orifice inputs")
    return coefficient * np.pi * diameter_m**2 / 4 * np.sqrt(2 * gravity * max(head_m, 0))


def evaluate(c, d, tilt=(0, 0), grid=None, fields=False):
    validate(c, d)
    nx, ny = grid or c["grid"]
    if min(nx, ny) < 5:
        raise ValueError("Grid too small")
    dx, dy = c["length_m"] / nx, c["width_m"] / ny
    x, y = np.meshgrid((np.arange(nx) + 0.5) * dx, (np.arange(ny) + 0.5) * dy)
    floor = floor_height(x, y, c, d)
    z = vertical_coordinates(x, y, floor, c["length_m"], c["width_m"], *tilt)
    rim = vertical_coordinates(x, y, c["wall_height_m"], c["length_m"], c["width_m"], *tilt)
    r = c["drain_diameter_m"] / 2
    mask = (x - d["drain_x_m"]) ** 2 + (y - c["width_m"] / 2) ** 2 <= r * r
    if not mask.any():
        raise ValueError("Grid does not resolve the outlet")
    center = float(
        vertical_coordinates(
            d["drain_x_m"],
            c["width_m"] / 2,
            floor_height(d["drain_x_m"], c["width_m"] / 2, c, d),
            c["length_m"],
            c["width_m"],
            *tilt,
        )
    )
    a, b = np.radians(tilt)
    gx = np.sin(a) + np.cos(a) * np.cos(b) * d["longitudinal_slope"]
    gy = np.cos(a) * np.sin(b)
    sill = center - r * np.hypot(gx, gy)
    terrain = np.where(mask, sill, z)
    seeds = [(int(i), int(j), sill) for i, j in zip(*np.where(mask), strict=True)]
    for i in range(ny):
        seeds.extend([(i, 0, rim[i, 0]), (i, nx - 1, rim[i, -1])])
    for j in range(nx):
        seeds.extend([(0, j, rim[0, j]), (ny - 1, j, rim[-1, j])])
    spill = spill_surface(terrain, seeds)
    depth = np.maximum(spill - z, 0)
    depth[mask] = 0
    cosine = np.cos(a) * np.cos(b)
    volume = float(depth.sum() * dx * dy / cosine)
    result = {
        "longitudinal_tilt_deg": tilt[0],
        "transverse_tilt_deg": tilt[1],
        "retained_capacity_ml": volume * 1e6,
        "maximum_vertical_depth_mm": float(depth.max() * 1000),
        "outlet_sill_global_mm": float(sill * 1000),
        "outlet_reference_head_mm": c["reference_head_m"] * 1000,
        "ideal_discharge_ml_s": discharge(
            c["reference_head_m"],
            c["drain_diameter_m"],
            c["discharge_coefficient"],
            c["gravity_m_s2"],
        )
        * 1e6,
        "nx": nx,
        "ny": ny,
    }
    if fields:
        return result, {
            "x": x,
            "y": y,
            "floor": floor,
            "potential": z,
            "spill": spill,
            "depth": depth,
            "hole": mask,
        }
    return result
