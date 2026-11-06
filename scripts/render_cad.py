import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

root = Path(__file__).resolve().parents[1]
fig = plt.figure(figsize=(12, 4.5))
for i, name in enumerate(["flat", "single_slope", "dual_slope"]):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d")
    data = json.loads((root / "cad/exports" / name / "triangles.json").read_text())
    polygons = np.array(data["points_mm"])[np.array(data["triangles"])]
    normals = np.cross(polygons[:, 1] - polygons[:, 0], polygons[:, 2] - polygons[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    intensity = LightSource(azdeg=315, altdeg=45).shade_normals(normals)
    base = np.array(to_rgb(["#8fb9cb", "#67aaa8", "#3d8b82"][i]))
    colors = base * (0.4 + 0.6 * intensity[:, None])
    ax.add_collection3d(Poly3DCollection(polygons, facecolors=colors, edgecolor="none"))
    ax.set(
        xlim=(-5, 325),
        ylim=(-5, 225),
        zlim=(-15, 28),
        xlabel="x [mm]",
        ylabel="y [mm]",
        zlabel="z [mm]",
        title=name.replace("_", " "),
    )
    ax.set_box_aspect((330, 230, 70))
    ax.view_init(38, -50)
    ax.tick_params(labelsize=7)
    for label in [ax.xaxis.label, ax.yaxis.label, ax.zaxis.label]:
        label.set_size(8)
fig.suptitle("FreeCAD tray solids · shared dimensions · vertical display scale enlarged")
fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.1, wspace=0.18)
fig.savefig(root / "results/cad_comparison.png", dpi=170, bbox_inches="tight")
