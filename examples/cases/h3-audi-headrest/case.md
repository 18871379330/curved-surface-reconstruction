# Case H3 Audi Headrest Cushion

This case captures lessons from reconstructing a soft headrest cushion from a multi-part STL/FBX-derived source. It is intended as a general reference for freeform cushion, pillow, pad, and ergonomic soft-body reverse modeling.

## Target

Reconstruct the main smooth cushion body as a single solid part.

Do not fit accessory/detail geometry into the main body:

- rear elastic straps;
- seam loops and stitch-like lines;
- thin bands and decorative strips;
- small detached or high-aspect-ratio fragments.

## Key Lesson

Treat the source as a scene, not as one object. The most common failure was fitting all STL geometry that happened to be present. That pulled rear straps and thin bands into the loft envelope and produced a back-side bulge that did not belong to the cushion body.

The second common failure was trying to solve side truncation by shrinking several real end sections into a cap. That discarded visible cushion mass. First extend real section coverage; only the tiny residual tail should be capped or filleted.

## Source Selection

Raw mesh candidate inspection showed multiple parts. The final reconstruction should start from the curated cushion-shell reference:

```text
input/quersus_h3_audi_cushion_shell_only.stl
```

This shell reference is already filtered compared with the full headrest export. It is closer to the main cushion body than using all candidate meshes.

Useful inspection files:

```text
input/poduszka_zaglowkowa_audi_mesh_summary.tsv
input/poduszka_zaglowkowa_audi_candidate_contact_sheet.png
input/h3_candidate_mesh_scene_summary.tsv
input/h3_candidate_mesh_scene_contact_sheet.png
input/h3_full_headrest_split_scene_summary.tsv
input/h3_full_headrest_split_contact_sheet.png
```

The `h3_candidate_mesh_scene_*` files are produced by the general `core/mesh_scene_inspector.py` tool on the extracted mesh-candidate directory. The `h3_full_headrest_split_scene_*` files are produced from the single full-headrest STL with `--split-components`, showing how to inspect a scene even when all parts are packed into one STL.

## Route

```text
curated cushion shell STL
-> inspect candidate components and reject accessory geometry
-> choose left-to-right section axis
-> fit each section as a closed wire made from multiple spline edges
   back surface spline + top connector spline + front surface spline + bottom connector spline
-> loft ordered section wires into one BREP solid
-> export STEP
-> import into SolidWorks and verify one solid body
```

## Best Baseline

The best visual baseline from the iteration was:

```text
outputs/h3_audi_spline_fitted_pillow_single_solid_baseline.SLDPRT
outputs/h3_audi_spline_fitted_pillow_single_solid_baseline.step
outputs/h3_audi_spline_fitted_pillow_single_solid_baseline_preview.png
```

It used the same spline-section method and avoided overfitting rear accessories. Its main weakness was visible flat side truncation.

## Retained Extended-Section Output

The retained extended-section output is:

```text
outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid.SLDPRT
outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid.step
outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid_preview.png
```

It extends the real section range while keeping the same main-body spline-section approach.

Validation from the run:

```text
VALID True
SOLIDS 1
STEP_REOPEN_SOLIDS 1
STEP_REOPEN_VALID True
FINAL_SOLID_BODIES=1
VERIFIED_SINGLE_SOLID=True
```

Section range evidence:

```text
source_range: 262.83233642578125 to 570.6513671875
sample_range: 262.9924621582031 to 570.4489135742188
uncovered axis span: about 0.118% of bbox width
```

## Rebuild Command

Run from the workspace root:

```powershell
python curved-surface-reconstruction\examples\cases\h3-audi-headrest\case-code\build_h3_audi_spline_pillow.py `
  --reference-stl curved-surface-reconstruction\examples\cases\h3-audi-headrest\input\quersus_h3_audi_cushion_shell_only.stl `
  --out-dir curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work `
  --basename h3_audi_spline_fitted_extended_real_sections_pillow_single_solid `
  --sections 45 `
  --z-points 23 `
  --x-coverage 0.998 `
  --end-cap-sections 0
```

## Inspection Commands

Run from the workspace root:

```powershell
python curved-surface-reconstruction\core\mesh_scene_inspector.py `
  "headrest_extraction\mesh_candidates\poduszka zaglowkowa audi" `
  --out-json curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work\mesh_scene_report.json `
  --out-tsv curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work\mesh_scene_summary.tsv `
  --contact-sheet curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work\mesh_scene_contact_sheet.png
```

```powershell
python curved-surface-reconstruction\core\mesh_scene_inspector.py `
  headrest_extraction\final_headrest_exports\quersus_h3_audi_full_headrest.stl `
  --split-components `
  --out-json curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work\full_headrest_split_scene_report.json `
  --out-tsv curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work\full_headrest_split_scene_summary.tsv `
  --contact-sheet curved-surface-reconstruction\examples\cases\h3-audi-headrest\_work\full_headrest_split_contact_sheet.png
```

In the directory inspection, the tool now de-duplicates same-stem OBJ/STL pairs and reports 8 mesh candidates instead of 16 duplicated format variants. It flags the seam-loop mesh as `accessory_or_detail_candidate` because it has large span but very low surface-area density and very low bbox volume fill.

## What Not To Repeat

Do not use all mesh candidates simply to cover more bbox span. In this case, including the upper band, rear thin surface, straps, or seam loops caused the fitted solid to capture non-cushion details.

Do not force sections into ellipses. The cushion has concave top curvature, asymmetric side bulges, and saddle-like thickness changes. Ellipse envelopes made the object look generic.

Do not confuse valid BREP with a correct reconstruction. Several outputs were valid single solids but visually wrong because the wrong components were fitted.

Do not overuse end caps. If caps start several sections inward, the result throws away the left and right cushion mass. Only cap the residual tail after real sections cover the target body.

Do not accept a later version just because it is more automated. Compare with the best prior visual baseline and make the smallest correction.

## General Rule Extracted

For a multi-part freeform STL:

1. Build a mesh/component summary and contact sheet.
2. Choose the intended main body by design intent.
3. Exclude accessory/detail components before fitting.
4. Define coverage on the selected main body, not the whole scene.
5. Use multi-segment spline wires for each section when the contour is not simple.
6. Keep the largest main-body loop by default when exact slicing returns multiple loops.
7. Validate with source/output views and section previews, not only topology checks.
