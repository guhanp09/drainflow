# Manufacture, service and proposed water test

The native CAD uses a thin floor shell rather than filling a thick solid wedge. Three tray solids include an 8 mm drain, 12 mm outer-diameter spigot, 10 mm spigot length and external 2 mm corner fillets. Minimum normal floor thickness is 2 mm. A 5 mm shoulder ramp joins the recessed channel to the outer floor planes. Dimensions and unthreaded interfaces are representative.

The 18 mm selected channel provides cleaning access. Keep the outlet reachable from below and provide clearance for the actual hose/clamp and servicing tool; verify those purchased interfaces before release. The model's 3 mm boss-to-wall clearance is a geometry constraint, not proof of service accessibility in an appliance.

The solid has zero mold draft and sharp internal shoulder transitions. Review draft, internal radii, shrinkage, gates, ejection and uniformity with the intended molding process before tooling. The underside offset limits floor-thickness variation; the local outlet boss still needs molding review. For an initial printed prototype, use STEP or correctly scale metre-unit STL by 1000 for a millimetre slicer, orient to support the sloping floor, check watertightness, and characterize print texture and warpage. The tray footprint requires a sufficiently large printer or a sealed segmented prototype.

Run `drainflow`, then regenerate CAD, then run the analysis again to include checked CAD material volumes. Native GUI edits change geometry; update the JSON and rerun the analysis to keep the numerical study synchronized.

## Proposed experiment

1. Measure the printed floor, drain and installation tilt. Verify the outlet and hose are unobstructed and use the same support and collection setup for each design.
2. Tare tray and collection vessel on a calibrated balance. Record water temperature, balance uncertainty and tilt uncertainty.
3. Wet the complete floor reproducibly. A temporarily plugged drain can establish an initial water level below the lowest rim; then open it. Avoid overflow, and record added and collected masses.
4. Test the five specified installation conditions. Use a stated settling time and repeat each test. Weigh retained water separately; allow for evaporation, external droplets and absorbed surface water.
5. Compare the large geometric differences first. The sub-0.02 mL ideal model result is below ordinary bench resolution and excludes wetting films, so do not interpret it as a measured dry tray.

The CSV under `examples/` is an empty future-measurement template. No experiment, contact-angle calibration or clogging test has been performed.
