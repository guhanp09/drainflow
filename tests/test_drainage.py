import copy

import numpy as np
import pytest

from drainflow.drainage import discharge, evaluate, spill_surface, vertical_coordinates
from drainflow.geometry import floor_height, floor_vertical_thickness, load, validate


def test_level_flat_has_no_geometric_puddle():
    c = load()
    r = evaluate(c, c["designs"]["flat"])
    assert r["retained_capacity_ml"] == 0 and r["maximum_vertical_depth_mm"] == 0


def test_known_enclosed_basin_and_escape_barrier():
    terrain = np.array(
        [[0, 0, 0, 0, 0], [0, 3, 3, 3, 0], [0, 3, 1, 3, 0], [0, 3, 3, 3, 0], [0, 0, 0, 0, 0]], float
    )
    spill = spill_surface(terrain, [(0, 0, 0)])
    assert spill[2, 2] == 3
    assert np.maximum(spill - terrain, 0).sum() == 2
    terrain[1, 2] = 1
    assert spill_surface(terrain, [(0, 0, 0)])[2, 2] == 1


def test_rim_exit_limits_a_basin():
    z = np.array([[0, 4, 0], [4, 0, 4], [0, 4, 0]], float)
    assert spill_surface(z, [(1, 1, 2)])[1, 1] == 2


def test_flat_tilt_matches_analytical_wedge_with_point_drain():
    c = load()
    d = c["designs"]["flat"]
    # Finite circular outlet is lower than the center point; compare exact lip head.
    result = evaluate(c, d, (0, 2), (321, 221))
    head = np.sin(np.radians(2)) * (c["width_m"] / 2 - c["drain_diameter_m"] / 2)
    exact = c["length_m"] * head**2 / (2 * np.sin(np.radians(2)) * np.cos(np.radians(2))) * 1e6
    assert result["retained_capacity_ml"] == pytest.approx(exact, rel=0.03)


def test_rotation_and_volume_coordinate_factor():
    assert vertical_coordinates(0.32, 0.11, 0.01, 0.32, 0.22, 0, 0) == 0.01
    actual = vertical_coordinates(0.32, 0.11, 0.01, 0.32, 0.22, 1, 0)
    assert actual == pytest.approx(0.16 * np.sin(np.radians(1)) + 0.01 * np.cos(np.radians(1)))


def test_tilt_reveals_flat_tray_weakness_and_dual_reduces_it():
    c = load()
    flat = evaluate(c, c["designs"]["flat"], (-1, 0))["retained_capacity_ml"]
    dual = evaluate(c, c["designs"]["dual_slope"], (-1, 0))["retained_capacity_ml"]
    assert flat > 100 and 0 <= dual < flat * 0.01
    assert evaluate(c, c["designs"]["flat"], (0, 2))["retained_capacity_ml"] == pytest.approx(
        evaluate(c, c["designs"]["flat"], (0, -2))["retained_capacity_ml"]
    )


def test_cross_profile_and_normal_floor_thickness():
    c = load()
    d = c["designs"]["dual_slope"]
    t = floor_vertical_thickness(c, d)
    slope = d["transverse_slope"] + d["channel_depth_m"] / c["shoulder_width_m"]
    assert t / np.sqrt(1 + slope * slope + d["longitudinal_slope"] ** 2) == pytest.approx(
        c["minimum_thickness_m"]
    )
    assert floor_height(0, 0.11, c, d) == 0
    assert floor_height(0.32, 0.11, c, d) == pytest.approx(0.32 * d["longitudinal_slope"])


@pytest.mark.parametrize("head", [0, -0.001, -1])
def test_nonpositive_orifice_head(head):
    assert discharge(head, 0.008) == 0


def test_orifice_area_and_head_scaling():
    assert discharge(0.02, 0.008) == pytest.approx(2 * discharge(0.005, 0.008))
    assert discharge(0.005, 0.016) == pytest.approx(4 * discharge(0.005, 0.008))


@pytest.mark.parametrize(
    "change", [{"length_m": -1}, {"outer_corner_fillet_m": 0.01}, {"drain_diameter_m": 0.02}]
)
def test_invalid_geometry(change):
    c = copy.deepcopy(load())
    c.update(change)
    with pytest.raises(ValueError):
        validate(c, c["designs"]["dual_slope"])


def test_unphysical_tilt_or_grid_is_rejected():
    c = load()
    with pytest.raises(ValueError):
        evaluate(c, c["designs"]["flat"], (90, 0))
    with pytest.raises(ValueError):
        evaluate(c, c["designs"]["flat"], grid=(2, 2))
