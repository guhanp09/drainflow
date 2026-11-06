"""FreeCAD thin-shell trays built from the same piecewise-planar floor definition."""

import json

import numpy as np

from drainflow.geometry import (
    ROOT,
    cross_profile,
    estimated_material_volume,
    floor_height,
    floor_vertical_thickness,
    load,
    validate,
)


def modules():
    import FreeCAD as App
    import Part

    return App, Part


def shape(c, d):
    validate(c, d)
    App, Part = modules()
    v = App.Vector
    length, width, height = [1000 * c[k] for k in ["length_m", "width_m", "wall_height_m"]]
    t = c["minimum_thickness_m"] * 1000
    tv = floor_vertical_thickness(c, d) * 1000
    outer = Part.makeBox(length + 2 * t, width + 2 * t, height + tv, v(-t, -t, -tv))
    edges = [
        e
        for e in outer.Edges
        if len(e.Vertexes) == 2
        and abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) < 1e-7
        and abs(e.Vertexes[0].Point.y - e.Vertexes[1].Point.y) < 1e-7
    ]
    if c["outer_corner_fillet_m"] > 0:
        outer = outer.makeFillet(c["outer_corner_fillet_m"] * 1000, edges)
    tray = outer.cut(Part.makeBox(length, width, height + 1, v(0, 0, 0)))
    additions = []
    slope = d["longitudinal_slope"]
    if slope > 0:
        face = Part.Face(
            Part.makePolygon(
                [v(0, 0, 0), v(length, 0, 0), v(length, 0, slope * length), v(0, 0, 0)]
            )
        )
        additions.append(face.extrude(v(0, width, 0)))
    ys, zs = cross_profile(c, d)
    ys, zs = ys * 1000, zs * 1000
    for y0, y1, z0, z1 in zip(ys[:-1], ys[1:], zs[:-1], zs[1:], strict=True):
        if max(z0, z1) < 1e-8:
            continue
        raw = [v(0, y0, 0), v(0, y1, 0), v(0, y1, z1), v(0, y0, z0)]
        points = []
        for point in raw:
            if not points or (point - points[-1]).Length > 1e-8:
                points.append(point)
        if (points[-1] - points[0]).Length < 1e-8:
            points.pop()
        additions.append(
            Part.Face(Part.makePolygon(points + [points[0]])).extrude(v(length, 0, slope * length))
        )
    if additions:
        fill = additions[0] if len(additions) == 1 else additions[0].multiFuse(additions[1:])
        tray = tray.fuse(fill)
        underside = fill.copy()
        underside.translate(v(0, 0, -tv))
        tray = tray.cut(underside)
    x, y = d["drain_x_m"] * 1000, width / 2
    drain_floor = float(floor_height(x / 1000, y / 1000, c, d)) * 1000
    spigot_bottom = drain_floor - tv - c["spigot_length_m"] * 1000
    boss = Part.makeCylinder(
        c["spigot_outer_diameter_m"] * 500, c["spigot_length_m"] * 1000 + 1, v(x, y, spigot_bottom)
    )
    tray = tray.fuse(boss).cut(
        Part.makeCylinder(
            c["drain_diameter_m"] * 500, height - spigot_bottom + 2, v(x, y, spigot_bottom - 1)
        )
    )
    return tray.removeSplitter()


class Tray:
    def execute(self, obj):
        c = json.loads(obj.Configuration)
        d = json.loads(obj.Design)
        for prop, key in [
            ("Length", "length_m"),
            ("Width", "width_m"),
            ("WallHeight", "wall_height_m"),
            ("Thickness", "minimum_thickness_m"),
            ("DrainDiameter", "drain_diameter_m"),
            ("OuterFillet", "outer_corner_fillet_m"),
            ("ManufacturingClearance", "manufacturing_clearance_m"),
        ]:
            c[key] = getattr(obj, prop).Value / 1000
        for prop, key in [
            ("DrainX", "drain_x_m"),
            ("ChannelWidth", "channel_width_m"),
            ("ChannelDepth", "channel_depth_m"),
        ]:
            d[key] = getattr(obj, prop).Value / 1000
        d["longitudinal_slope"] = obj.LongitudinalSlope
        d["transverse_slope"] = obj.TransverseSlope
        obj.Shape = shape(c, d)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def drawing(name, c, d, path):
    length, width = c["length_m"] * 1000, c["width_m"] * 1000
    dx = d["drain_x_m"] * 1000
    half = d["channel_width_m"] * 500
    channel_lines = ""
    channel_label = "No recessed channel in this reference geometry"
    if d["channel_depth_m"] > 0 or d["transverse_slope"] > 0:
        for yy in [110 + width - 2 * half, 110 + width + 2 * half]:
            channel_lines += (
                f'<line x1="50" y1="{yy}" x2="{50 + 2 * length}" y2="{yy}" class="line"/>'
            )
        channel_label = (
            f"Channel {2 * half:.1f} wide; recess {d['channel_depth_m'] * 1000:.1f}; "
            f"shoulder ramp {c['shoulder_width_m'] * 1000:.1f}; draft not modeled"
        )
    text = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="760" viewBox="0 0 900 760">
<rect width="900" height="760" fill="white"/>
<style>text{{font-family:Arial;fill:#183447}} .line{{stroke:#183447;fill:none;stroke-width:2}}</style>
<text x="35" y="35" font-size="24">DrainFlow — {name}</text>
<text x="35" y="60" font-size="14">Dimensions mm · inner floor {length:.0f}×{width:.0f} · outer corner fillet R{c["outer_corner_fillet_m"] * 1000:.1f}</text>
<rect x="46" y="106" width="{2 * length + 8}" height="{2 * width + 8}" rx="4" class="line"/>
<rect x="50" y="110" width="{2 * length}" height="{2 * width}" class="line"/>
<circle cx="{50 + 2 * dx}" cy="{110 + width}" r="{c["drain_diameter_m"] * 1000}" class="line"/>
{channel_lines}
<text x="705" y="200">Wall {c["minimum_thickness_m"] * 1000:.1f}</text>
<text x="705" y="225">Height {c["wall_height_m"] * 1000:.0f}</text>
<text x="50" y="580">Drain Ø{c["drain_diameter_m"] * 1000:.0f}; center x={dx:.1f}, y={width / 2:.1f}; spigot OD {c["spigot_outer_diameter_m"] * 1000:.0f}</text>
<line x1="50" y1="620" x2="{50 + 2 * length}" y2="620" class="line"/>
<line x1="50" y1="670" x2="{50 + 2 * length}" y2="{670 - 2 * length * d["longitudinal_slope"]}" class="line"/>
<text x="50" y="705">Center section: long slope {d["longitudinal_slope"]:.3f}; transverse slope {d["transverse_slope"]:.3f}</text>
<text x="50" y="730">{channel_label}</text>
</svg>'''
    path.write_text(text)


def export_all():
    App, Part = modules()
    import Mesh

    c = load()
    designs = dict(c["designs"])
    selected = ROOT / "results/selected_design.json"
    if not selected.exists():
        raise ValueError("Run drainflow before exporting the selected designs")
    designs["dual_slope"] = json.loads(selected.read_text())
    for name, d in designs.items():
        out = ROOT / "cad/exports" / name
        out.mkdir(parents=True, exist_ok=True)
        doc = App.newDocument("DrainFlow_" + name)
        obj = doc.addObject("Part::FeaturePython", "Tray")
        obj.addProperty("App::PropertyString", "Configuration").Configuration = json.dumps(c)
        obj.addProperty("App::PropertyString", "Design").Design = json.dumps(d)
        for prop, key in [
            ("Length", "length_m"),
            ("Width", "width_m"),
            ("WallHeight", "wall_height_m"),
            ("Thickness", "minimum_thickness_m"),
            ("DrainDiameter", "drain_diameter_m"),
            ("OuterFillet", "outer_corner_fillet_m"),
            ("ManufacturingClearance", "manufacturing_clearance_m"),
        ]:
            obj.addProperty("App::PropertyLength", prop, "Geometry")
            setattr(obj, prop, c[key] * 1000)
        for prop, key in [
            ("DrainX", "drain_x_m"),
            ("ChannelWidth", "channel_width_m"),
            ("ChannelDepth", "channel_depth_m"),
        ]:
            obj.addProperty("App::PropertyLength", prop, "Geometry")
            setattr(obj, prop, d[key] * 1000)
        obj.addProperty("App::PropertyFloat", "LongitudinalSlope").LongitudinalSlope = d[
            "longitudinal_slope"
        ]
        obj.addProperty("App::PropertyFloat", "TransverseSlope").TransverseSlope = d[
            "transverse_slope"
        ]
        obj.Proxy = Tray()
        doc.recompute()
        solid = obj.Shape
        if not solid.isValid() or len(solid.Solids) != 1 or solid.Volume <= 0:
            raise ValueError("Invalid tray solid")
        errors = []
        normal_thickness = []
        for x in np.array([0.04, 0.3, 0.75, 0.95]) * c["length_m"]:
            for y in list(np.array([0.03, 0.25, 0.47, 0.53, 0.75, 0.97]) * c["width_m"]) + [
                c["width_m"] / 2 - d["channel_width_m"] / 2 - c["shoulder_width_m"] / 2,
                c["width_m"] / 2 + d["channel_width_m"] / 2 + c["shoulder_width_m"] / 2,
            ]:
                if (
                    np.hypot(x - d["drain_x_m"], y - c["width_m"] / 2)
                    < c["drain_diameter_m"] / 2 + 0.001
                ):
                    continue
                section = solid.section(
                    Part.makeLine(
                        App.Vector(x * 1000, y * 1000, -30), App.Vector(x * 1000, y * 1000, 35)
                    )
                )
                actual = max(v.Point.z for v in section.Vertexes) / 1000
                errors.append(abs(actual - float(floor_height(x, y, c, d))))
                measured = (
                    max(v.Point.z for v in section.Vertexes)
                    - min(v.Point.z for v in section.Vertexes)
                ) / 1000
                q = abs(y - c["width_m"] / 2) - d["channel_width_m"] / 2
                gradient = (
                    0
                    if q < 0
                    else d["transverse_slope"]
                    + (
                        d["channel_depth_m"] / c["shoulder_width_m"]
                        if q < c["shoulder_width_m"]
                        else 0
                    )
                )
                normal_thickness.append(
                    measured / np.sqrt(1 + d["longitudinal_slope"] ** 2 + gradient**2)
                )
        if max(errors) > 1e-7 or min(normal_thickness) < c["minimum_thickness_m"] - 1e-7:
            raise ValueError("CAD floor or thickness differs from the analysis geometry")
        Part.export([obj], str(out / (name + ".step")))
        matrix = App.Matrix()
        matrix.scale(0.001, 0.001, 0.001)
        solid.transformGeometry(matrix).exportStl(str(out / (name + "_m.stl")))
        points, triangles = solid.tessellate(0.3)
        (out / "triangles.json").write_text(
            json.dumps({"points_mm": [[p.x, p.y, p.z] for p in points], "triangles": triangles})
        )
        checks = {
            "design": d,
            "config": c,
            "valid_solid": True,
            "volume_m3": solid.Volume * 1e-9,
            "estimated_material_m3": float(estimated_material_volume(c, d)),
            "maximum_floor_height_error_m": max(errors),
            "floor_samples": len(errors),
            "minimum_normal_floor_thickness_m": min(normal_thickness),
            "vertical_floor_thickness_m": float(floor_vertical_thickness(c, d)),
            "step_reimport_valid": Part.read(str(out / (name + ".step"))).isValid(),
            "stl_x_extent_m": Mesh.Mesh(str(out / (name + "_m.stl"))).BoundBox.XLength,
            "freecad_version": ".".join(App.Version()[:3]),
        }
        if abs(checks["stl_x_extent_m"] - (c["length_m"] + 2 * c["minimum_thickness_m"])) > 1e-5:
            raise ValueError("STL scale mismatch")
        if abs(checks["volume_m3"] / checks["estimated_material_m3"] - 1) > 0.02:
            raise ValueError("Thin-shell material estimate disagrees with CAD")
        doc.saveAs(str(out / (name + ".FCStd")))
        drawing(name, c, d, out / "drawing.svg")
        volume = solid.Volume
        obj.Length = c["length_m"] * 1000 + 1
        obj.touch()
        doc.recompute()
        checks["editable_length_recompute"] = obj.Shape.Volume > volume
        App.closeDocument(doc.Name)
        restored = App.openDocument(str(out / (name + ".FCStd")))
        restored.recompute()
        checks["native_reopen_valid"] = restored.getObject("Tray").Shape.isValid()
        App.closeDocument(restored.Name)
        if (
            not checks["editable_length_recompute"]
            or not checks["native_reopen_valid"]
            or not checks["step_reimport_valid"]
        ):
            raise ValueError("Native/STEP check failed")
        (out / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
        print(name, "valid thin-shell tray; floor error", max(errors), "m")
