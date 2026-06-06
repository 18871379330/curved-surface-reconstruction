# Tool-Agnostic Curved Surface Reconstruction Workflow

## 1. Intake

Record:

- source file type and units;
- user authorization or ownership;
- target output format;
- whether editability or one complete solid is more important;
- tolerance target, such as max surface deviation or visual-only concept.

Create a backup before modifying any file.

## 2. Generic Inspection

For meshes and point clouds:

- bounding box and scale;
- point/vertex/triangle count;
- open edges;
- nonmanifold edges;
- degenerate faces;
- signed volume and positive volume;
- rough target-surface location.

For multi-part meshes:

- list mesh/body components with triangle count, vertex count, bbox, aspect ratio, and visual preview;
- use `core/mesh_scene_inspector.py` to create a JSON/TSV report and contact sheet before profile fitting;
- for one STL/OBJ containing multiple detached shells, run the inspector with `--split-components`;
- classify each component as main body, candidate surface, accessory, seam/detail, support hardware, or reject;
- preserve the source but build the reconstruction only from the selected target body;
- record exactly which mesh ids or bodies were included and excluded.

For CAD/BREP:

- body count;
- face count;
- closed/open shell state;
- invalid/failed faces;
- whether the target face is already a single face.

## 3. Core Reconstruction

Core should not depend on a CAD brand.

Recommended core route:

1. Normalize coordinates.
2. Identify target face, region, or primary body by design intent.
3. Reject accessory geometry before fitting. Use size, aspect ratio, surface-area density, volume-fill ratio, connected-shell contact sheets, and user intent together; do not let straps, seams, stitches, labels, zippers, brackets, thin sheets, or decorative patches define the main-body envelope unless requested.
4. Choose a section axis and coverage rule.
5. Sample points, exact plane intersections, or section curves from the selected body.
6. Reject outliers and non-main-body loops.
7. Fit a low-degree polynomial, spline, NURBS, or patch network.
8. Generate ordered profiles with consistent point order and persistent landmarks.
9. Emit profile JSON and fit report.

Profile quality matters more than point count. Too many noisy points can create worse CAD topology than fewer smooth profiles.

### Section Coverage

Coverage must be defined on the intended target body, not on every mesh fragment in the file.

- State whether the 99% range is bbox-based or quantile-based.
- Bbox-based coverage preserves geometric end span; quantile-based coverage rejects sparse end outliers but may stop short on tapered geometry.
- When users complain about side truncation, first inspect the actual section range against the target-body bbox.
- Use real sections over nearly all of the target range. Only the final small remainder should become a cap or fillet.
- If exact slicing gives multiple closed loops, choose the largest main-body loop by default. Keep additional loops only when they are true main-body holes or features.
- If a section has concavity or asymmetric thickness, use multiple spline edges in one closed wire instead of forcing one ellipse or one envelope curve.

### End Caps

Rounded ends should solve only the residual tail problem.

- Avoid scaling down several real end sections; this discards the very geometry the fit is supposed to preserve.
- Prefer extra tiny cap sections outside or at the last validated target-body section.
- If a cap creates a thinner or worse-looking body than the uncapped version, keep the uncapped best-fit body and report the remaining side flatness.
- Fillet only the actual end edges when possible; do not fillet every loft edge blindly.

## 4. Build Routes

### Route A: Feature-Native CAD

Use when the user primarily needs parametric editability.

Pattern:

- create reference planes;
- create section sketches;
- draw simple closed profiles;
- use one or more spline segments for freeform edges;
- loft or boundary-surface between profiles;
- name features by construction role;
- rebuild and inspect.

Risk: native lofts may fragment into multiple bodies or fail to combine.

Important: a sketch plane may contain more than one closed contour. Keep the largest contour when only the main body is needed. Use multiple contours only for true main-body holes/features, not accessory parts.

### Route B: Single BREP Solid

Use when the user primarily needs one selectable/exportable body.

Pattern:

- build closed profile wires from core profile JSON;
- loft profiles with OCC/CadQuery/FreeCAD;
- sew/solidify if needed;
- export STEP;
- verify solid validity, face count, and volume.

This route is usually less feature-editable but more reliable for a complete handoff body.

Do not treat a valid single solid as visually correct by itself. A single BREP can still be a poor reconstruction if the wrong components were included or if the section range missed the main body's ends.

### Route C: Mesh Repair

Use when input is noisy or the task only requires visual/print proof.

Pattern:

- clean mesh;
- fill holes;
- remove self-intersections where possible;
- remesh/smooth;
- export STL/OBJ/PLY;
- label quality as mesh-only.

Do not present a mesh-only result as a parametric CAD solid.

## 5. Failure Fallbacks

Use this fallback order:

1. Native feature reconstruction.
2. Single BREP/STEP reconstruction from fitted profiles.
3. Surface-only BREP with explicit open-shell label.
4. Repaired mesh with explicit mesh-only label.

Always report which quality level was achieved.

## 6. Validation

Generic validation:

- watertight/manifold for meshes;
- valid BREP status for OCC/CAD solids;
- positive volume;
- no obvious self-intersection;
- bounded fit error if reference samples exist;
- visual preview from at least one angle that shows the target surface.

Visual validation:

- compare source and output in matching isometric, front, side, and top views;
- inspect a contact sheet of representative section profiles;
- confirm that excluded accessories were not fitted into the body;
- confirm that the selected section range covers the intended target body, especially both ends of the section axis;
- compare against the best previous iteration before accepting a later one.

Adapter validation:

- CadQuery/OCC: `solid.isValid()`, `len(Solids()) == 1`, volume > 0.
- FreeCAD: shape validity, shell/solid count, exported STEP reopen.
- SolidWorks: reopened file body count and face count.

## 7. Delivery

Deliver:

- final reconstructed file;
- validation report;
- optional preview image;
- profile JSON or reconstruction parameters when useful;
- clear quality label Q0-Q4.

Keep final delivery clean. Put exploratory files in work or examples folders, not the user-facing result folder.

For section-based reconstructions, also deliver or retain:

- included/excluded component list;
- section-axis coverage numbers;
- slice/profile preview image;
- note on cap strategy and any residual flatness or accessory omission.
