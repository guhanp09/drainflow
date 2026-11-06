"""Tilt comparison, bounded robust design selection and engineering plots."""

import argparse
import csv
import itertools
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drainflow.drainage import evaluate
from drainflow.geometry import ROOT, estimated_material_volume, load, validate


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def worst(c, d, grid):
    return max(evaluate(c, d, t, grid)["retained_capacity_ml"] for t in c["tilts_deg"])


def optimize(c):
    keys = list(c["sweep"])
    rows = []
    for values in itertools.product(*(c["sweep"][key] for key in keys)):
        d = dict(c["designs"]["dual_slope"])
        d.update(dict(zip(keys, values, strict=True)))
        try:
            validate(c, d)
        except ValueError:
            continue
        rows.append(
            d
            | {
                "worst_retention_ml": worst(c, d, (81, 55)),
                "estimated_material_cm3": estimated_material_volume(c, d) * 1e6,
            }
        )
    if not rows:
        raise ValueError("No feasible tray designs")
    band = c["retention_indifference_ml"]
    best = min(r["worst_retention_ml"] for r in rows)
    eligible = [r for r in rows if r["worst_retention_ml"] <= best + band]

    def practical(r):
        return (r["estimated_material_cm3"], -r["channel_width_m"], abs(r["drain_x_m"] - 0.010))

    finalists = sorted(eligible, key=practical)[:5]
    refined = []
    for row in finalists:
        d = {key: row[key] for key in c["designs"]["dual_slope"]}
        refined.append(row | {"worst_retention_ml": worst(c, d, tuple(c["grid"]))})
    best = min(r["worst_retention_ml"] for r in refined)
    winner = min((r for r in refined if r["worst_retention_ml"] <= best + band), key=practical)
    return rows, {key: winner[key] for key in c["designs"]["dual_slope"]}, refined


def run(c, out):
    out.mkdir(parents=True, exist_ok=True)
    sweep, selected, refined = optimize(c)
    designs = dict(c["designs"])
    designs["dual_slope"] = selected
    rows = []
    fields = {}
    for name, d in designs.items():
        cad = ROOT / "cad/exports" / name / "checks.json"
        actual = None
        if cad.exists():
            check = json.loads(cad.read_text())
            if check["config"] == c and check["design"] == d:
                actual = check["volume_m3"] * 1e6
        for tilt in c["tilts_deg"]:
            metric, data = evaluate(c, d, tilt, fields=True)
            rows.append(
                {
                    "design": name,
                    **metric,
                    "estimated_material_cm3": estimated_material_volume(c, d) * 1e6,
                    "cad_material_cm3": actual,
                    "complexity": d["complexity"],
                }
            )
            fields[(name, tuple(tilt))] = data
    worsts = {
        name: max(r["retained_capacity_ml"] for r in rows if r["design"] == name)
        for name in designs
    }
    convergence = []
    for grid in [(81, 55), (161, 111), (321, 221)]:
        convergence.append(
            {"nx": grid[0], "ny": grid[1], "worst_retention_ml": worst(c, selected, grid)}
        )
    delta = abs(convergence[-1]["worst_retention_ml"] - convergence[-2]["worst_retention_ml"])
    summary = {
        "config": c,
        "designs": designs,
        "selected": selected,
        "worst_retention_ml": worsts,
        "reduction_vs_flat_pct": 100 * (1 - worsts["dual_slope"] / worsts["flat"]),
        "sweep_candidates": len(sweep),
        "refined_finalists": refined,
        "grid_convergence": convergence,
        "fine_grid_change_ml": delta,
        "grid_screen_passed": delta <= 1.0,
        "retention_definition": "Geometric capacity after sufficient wetting and gravity drainage; excludes films and capillarity",
        "physical_testing_performed": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (out / "selected_design.json").write_text(json.dumps(selected, indent=2) + "\n")
    write_csv(out / "comparison.csv", rows)
    write_csv(out / "parameter_sweep.csv", sweep)
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.2, "figure.figsize": (8, 4.6)})
    fig, ax = plt.subplots()
    for i, name in enumerate(designs):
        values = [r["retained_capacity_ml"] for r in rows if r["design"] == name]
        ax.bar(np.arange(5) + (i - 1) * 0.25, values, width=0.25, label=name.replace("_", " "))
    ax.set(
        xticks=np.arange(5),
        xticklabels=["level", "+1° long", "−1° long", "+2° trans", "−2° trans"],
        ylabel="Geometric retained-water capacity [mL]",
        title="Installation tilt sensitivity · grid 161×111",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "tilt_comparison.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
    maxdepth = max(data["depth"].max() for data in fields.values()) * 1000
    for ax, name in zip(axes, designs, strict=True):
        t = max((r for r in rows if r["design"] == name), key=lambda r: r["retained_capacity_ml"])
        data = fields[(name, (t["longitudinal_tilt_deg"], t["transverse_tilt_deg"]))]
        image = ax.pcolormesh(
            data["x"] * 1000,
            data["y"] * 1000,
            data["depth"] * 1000,
            vmin=0,
            vmax=maxdepth,
            cmap="Blues",
            shading="nearest",
        )
        ax.set(
            title=f"{name}\nworst tested tilt ({t['longitudinal_tilt_deg']}, {t['transverse_tilt_deg']})°",
            xlabel="x [mm]",
            ylabel="y [mm]",
            aspect="equal",
        )
    fig.colorbar(image, ax=axes, label="Vertical retained depth [mm]")
    fig.savefig(out / "retained_depth.png", dpi=160)
    plt.close(fig)
    d = selected
    data = fields[("dual_slope", (0, 0))]
    gy, gx = np.gradient(
        data["potential"], c["width_m"] / c["grid"][1], c["length_m"] / c["grid"][0]
    )
    fig, ax = plt.subplots()
    im = ax.pcolormesh(
        data["x"] * 1000, data["y"] * 1000, data["floor"] * 1000, shading="nearest", cmap="terrain"
    )
    skip = (slice(None, None, 9), slice(None, None, 10))
    magnitude = np.maximum(np.hypot(gx, gy), 1e-10)
    ax.quiver(
        data["x"][skip] * 1000,
        data["y"][skip] * 1000,
        (-gx / magnitude)[skip],
        (-gy / magnitude)[skip],
        color="#222222",
        scale=25,
    )
    ax.set(
        xlabel="x [mm]",
        ylabel="y [mm]",
        aspect="equal",
        title="Selected floor · arrows show downhill direction, not velocity",
    )
    fig.colorbar(im, ax=ax, label="Floor elevation [mm]")
    fig.tight_layout()
    fig.savefig(out / "floor_directions.png", dpi=160)
    plt.close(fig)
    report = f"""# DrainFlow engineering report

The comparison uses three geometries under level installation, ±1° longitudinal tilt, and ±2° transverse tilt. Water retention is a minimax spill-connectivity capacity after sufficient wetting, not a transient fluid simulation or a prediction of residual films.

| Geometry | Worst retained capacity [mL] |
|---|---:|
| Flat reference | {worsts["flat"]:.4f} |
| Single slope | {worsts["single_slope"]:.4f} |
| Selected dual slope/channel | {worsts["dual_slope"]:.4f} |

The selected dual design reduces the modeled worst-case geometric capacity by {summary["reduction_vs_flat_pct"]:.3f}%. Absolute near-zero values must be interpreted against grid resolution and omitted wetting physics; this percentage is not a measured drainage improvement.

## Selection

A bounded sweep evaluates {len(sweep)} feasible geometric combinations at 81×55 cells; five practical finalists are recomputed at the reporting grid. Designs within {c["retention_indifference_ml"]:.1f} mL of the minimum worst-case capacity are treated as engineering equivalents. Selection then minimizes the thin-shell material estimate, favors wider cleanable channels, and retains the standard outlet location where tied. This band is a design choice, not statistical confidence.

Selected longitudinal slope: {selected["longitudinal_slope"]:.3f}; transverse slope: {selected["transverse_slope"]:.3f}; channel width/depth: {selected["channel_width_m"] * 1000:.1f}/{selected["channel_depth_m"] * 1000:.1f} mm; outlet center x: {selected["drain_x_m"] * 1000:.1f} mm. The main floor retains a drainage bias under the specified tilt cases; small outlet/channel pockets remain in the geometric model.

The 161×111 to 321×221 grid change in worst retained capacity is {delta:.5f} mL, against a 1 mL screening tolerance. Source CSVs retain full numerical precision. CAD checks independently sample the actual solid floor and compare it with the analytical height field, verify minimum normal floor thickness and validate STEP/STL/native exports.

## Outlet and manufacture

At the assumed 5 mm head, Cd={c["discharge_coefficient"]} and an 8 mm drain give approximately {rows[0]["ideal_discharge_ml_s"]:.2f} mL/s from the ideal orifice equation. It omits inlet, hose, viscous, air-locking and clogging effects. It is not used to invent an emptying-time prediction.

The floor is a thin offset shell, not a thick wedge. Its vertical thickness is chosen so the minimum normal thickness is at least 2 mm at the steepest planar segment. The CAD includes an outlet spigot and outer corner fillets. Internal shoulder corners, zero draft and simplified interfaces require review before injection-mold tooling. The assembly/test guide covers service access and calibration. No physical water test was performed.
"""
    (out / "report.md").write_text(report)
    print(
        json.dumps(
            {
                "selected": selected,
                "worst_retention_ml": worsts,
                "fine_grid_change_ml": delta,
                "candidates": len(sweep),
            },
            indent=2,
        )
    )
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path)
    p.add_argument("--output", type=Path, default=ROOT / "results")
    a = p.parse_args()
    run(load(a.config), a.output)


if __name__ == "__main__":
    main()
