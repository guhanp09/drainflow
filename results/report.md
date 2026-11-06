# DrainFlow engineering report

The comparison uses three geometries under level installation, ±1° longitudinal tilt, and ±2° transverse tilt. Water retention is a minimax spill-connectivity capacity after sufficient wetting, not a transient fluid simulation or a prediction of residual films.

| Geometry | Worst retained capacity [mL] |
|---|---:|
| Flat reference | 179.7865 |
| Single slope | 13.9409 |
| Selected dual slope/channel | 0.0120 |

The selected dual design reduces the modeled worst-case geometric capacity by 99.993%. Absolute near-zero values must be interpreted against grid resolution and omitted wetting physics; this percentage is not a measured drainage improvement.

## Selection

A bounded sweep evaluates 162 feasible geometric combinations at 81×55 cells; five practical finalists are recomputed at the reporting grid. Designs within 1.0 mL of the minimum worst-case capacity are treated as engineering equivalents. Selection then minimizes the thin-shell material estimate, favors wider cleanable channels, and retains the standard outlet location where tied. This band is a design choice, not statistical confidence.

Selected longitudinal slope: 0.020; transverse slope: 0.040; channel width/depth: 18.0/1.0 mm; outlet center x: 10.0 mm. The main floor retains a drainage bias under the specified tilt cases; small outlet/channel pockets remain in the geometric model.

The 161×111 to 321×221 grid change in worst retained capacity is 0.00073 mL, against a 1 mL screening tolerance. Source CSVs retain full numerical precision. CAD checks independently sample the actual solid floor and compare it with the analytical height field, verify minimum normal floor thickness and validate STEP/STL/native exports.

## Outlet and manufacture

At the assumed 5 mm head, Cd=0.62 and an 8 mm drain give approximately 9.76 mL/s from the ideal orifice equation. It omits inlet, hose, viscous, air-locking and clogging effects. It is not used to invent an emptying-time prediction.

The floor is a thin offset shell, not a thick wedge. Its vertical thickness is chosen so the minimum normal thickness is at least 2 mm at the steepest planar segment. The CAD includes an outlet spigot and outer corner fillets. Internal shoulder corners, zero draft and simplified interfaces require review before injection-mold tooling. The assembly/test guide covers service access and calibration. No physical water test was performed.
