"""Shared SI floor definition used by the analysis and solid CAD."""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def load(path=None):
    return json.loads(Path(path or ROOT / "configs/baseline.json").read_text())


def cross_profile(c, d):
    width = c["width_m"]
    half = d["channel_width_m"] / 2
    shoulder = c["shoulder_width_m"]
    middle = width / 2
    if d["transverse_slope"] == 0 and d["channel_depth_m"] == 0:
        return np.array([0.0, width]), np.array([0.0, 0.0])
    ys = np.array(
        [0, middle - half - shoulder, middle - half, middle + half, middle + half + shoulder, width]
    )
    q = np.maximum(abs(ys - middle) - half, 0)
    z = d["transverse_slope"] * q + d["channel_depth_m"] * np.minimum(q / shoulder, 1)
    return ys, z


def floor_height(x, y, c, d):
    q = np.maximum(np.abs(np.asarray(y) - c["width_m"] / 2) - d["channel_width_m"] / 2, 0)
    return (
        d["longitudinal_slope"] * np.asarray(x)
        + d["transverse_slope"] * q
        + d["channel_depth_m"] * np.minimum(q / c["shoulder_width_m"], 1)
    )


def floor_vertical_thickness(c, d):
    max_cross = d["transverse_slope"] + d["channel_depth_m"] / c["shoulder_width_m"]
    return c["minimum_thickness_m"] * np.sqrt(1 + d["longitudinal_slope"] ** 2 + max_cross**2)


def validate(c, d):
    for key in [
        "length_m",
        "width_m",
        "wall_height_m",
        "minimum_thickness_m",
        "drain_diameter_m",
        "spigot_length_m",
        "shoulder_width_m",
    ]:
        if not np.isfinite(c[key]) or c[key] <= 0:
            raise ValueError("Positive finite dimensions required")
    if not all(np.isfinite(v) for v in d.values()):
        raise ValueError("Nonfinite design value")
    if min(d["longitudinal_slope"], d["transverse_slope"], d["channel_depth_m"]) < 0:
        raise ValueError("Negative design slope/depth")
    radius = c["spigot_outer_diameter_m"] / 2
    if c["spigot_outer_diameter_m"] <= c["drain_diameter_m"]:
        raise ValueError("Spigot wall missing")
    if (
        not radius + c["manufacturing_clearance_m"]
        <= d["drain_x_m"]
        <= c["length_m"] - radius - c["manufacturing_clearance_m"]
    ):
        raise ValueError("Outlet lacks wall clearance")
    if d["channel_width_m"] < c["drain_diameter_m"] + 2 * c["channel_fit_clearance_m"]:
        raise ValueError("Drain does not fit the channel")
    if d["channel_width_m"] + 2 * c["shoulder_width_m"] >= c["width_m"]:
        raise ValueError("Channel too wide")
    if not 0 <= c["outer_corner_fillet_m"] <= c["minimum_thickness_m"]:
        raise ValueError("Outer fillet exceeds wall allowance")
    highest = float(floor_height(c["length_m"], 0, c, d))
    if highest + c["minimum_freeboard_m"] >= c["wall_height_m"]:
        raise ValueError("Insufficient freeboard")


def estimated_material_volume(c, d):
    """Thin shell with vertical offset chosen to preserve minimum normal thickness."""
    t = c["minimum_thickness_m"]
    tv = floor_vertical_thickness(c, d)
    area = c["length_m"] * c["width_m"]
    outer = (c["length_m"] + 2 * t) * (c["width_m"] + 2 * t)
    r = c["drain_diameter_m"] / 2
    ro = c["spigot_outer_diameter_m"] / 2
    return (
        area * tv
        + (outer - area) * (c["wall_height_m"] + tv)
        + np.pi * (ro**2 - r**2) * c["spigot_length_m"]
        - np.pi * r**2 * tv
    )
