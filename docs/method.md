# Geometry and drainage model

All dimensions, installation scenarios and outlet coefficients are engineering assumptions. No water measurements are included.

## Shared floor

The interior is 320×220 mm, with a 25 mm rim and minimum 2 mm wall/floor thickness. The flat reference has z=0; the single slope has z=sx·x. The dual floor adds a center channel and two transverse planes. With q=max(|y−W/2|−w/2,0), the floor is

z(x,y)=sx·x+sy·q+d·min(q/b,1),

where w is channel width, d is channel recess and b=5 mm is the shoulder ramp. The ramp makes the profile continuous, without a vertical zero-thickness join. The same piecewise planes create the CAD solid and analysis grid.

The underside is offset vertically from this floor. To keep normal thickness at least t, the vertical offset is tv=t·sqrt(1+sx²+(sy+d/b)²). Outer walls have thickness t; external corner fillets are limited to t. CAD section checks sample both surfaces, verify normal thickness, and compare the solid's top floor against the analytical height field. STEP reimport, metre-unit STL bounds and native edit/reopen checks accompany each assembly.

## Tilt and volume

Positive longitudinal/transverse tilt raises the far x/y edge. For ordered rotations Ry(−a)Rx(b), the global vertical coordinate is

Z=sin(a)(x−L/2)+cos(a)sin(b)(y−W/2)+cos(a)cos(b)z.

The floor is sampled at cell centers. The outlet is represented by cells within its circular opening; its lowest lip elevation is evaluated from the local plane. Rim boundary cells provide a second escape path at the rotated rim elevation.

For each cell, the escape elevation is the minimum, over all connected paths to an outlet/rim, of the maximum elevation along the path. A multi-source minimax Dijkstra/priority-flood calculation on a four-neighbor graph finds these barriers. It identifies trapped depressions that a local gradient test can miss. The method follows the depression-filling principle described by [Barnes, Lehman and Mulla (2014)](https://rbarnes.org/sci/2014_depressions.pdf), adapted to tray outlets and rims.

Retained capacity is sum(max(Zescape−Zfloor,0)·dx·dy/[cos(a)cos(b)]), excluding the drain opening. The cosine factor converts global vertical water depth to the local-coordinate column volume; rotations preserve volume. This is capacity after sufficient wetting, not the residual from an arbitrary water dose. It assumes static hydrostatic pools and unrestricted gravity escape. Surface tension, contact angle, roughness, films, transient channel friction and clogging are omitted.

## Selection and resolution

All three designs are evaluated level, at ±1° longitudinal tilt and at ±2° transverse tilt. Simultaneous two-axis tilts are not part of the five-case comparison. A 162-combination dual-floor search varies both slopes, channel width/depth and outlet x position. Screening uses 81×55 cells; five material/cleanability finalists are recomputed at 161×111. A 1 mL worst-case indifference band precedes material minimization and preference for a wider cleanable channel and the standard outlet position. The band is an engineering choice, not a confidence interval.

The selected design is checked at 81×55, 161×111 and 321×221 cells. Circle/cell intersection, four-neighbor paths and midpoint area integration introduce grid error. Sub-millilitre computed differences do not establish actual dry-out performance. A future physical test must measure wetting residue and manufactured tolerances.

## Outlet flow

Q=Cd·A·sqrt(2gh) is evaluated at a separately assumed 5 mm head. Nonpositive head gives zero outflow. Cd=0.62 is illustrative; entrance shape, finite spigot length, viscosity, hoses, air locks and clogging can change discharge substantially. This estimate is not used as a transient free-surface simulation or an emptying-time prediction.
