---
name: curved-surface-reconstruction
description: AgentSkill for tool-agnostic curved-surface and closed-solid reconstruction from authorized STL, OBJ, ASCII PLY, point samples, and CAD-adapter inputs. Use when an agent must inspect geometry, separate the intended main body from accessory/detail parts, fit ordered sections or surface profiles, export CAD-ready STEP/STL outputs through adapters, and return validation evidence. This skill is especially relevant for freeform cushions, pads, ergonomic products, curved blocks, shells, and other reverse-modeling tasks that require traceable decisions rather than a direct mesh-to-solid conversion.
---

# Curved Surface Reconstruction AgentSkill

## Purpose

Use this AgentSkill to guide an AI agent through a disciplined reverse-modeling workflow for curved products, soft goods, and closed solids. The skill is not a single automatic converter. It is an operating procedure for choosing the right reconstruction route, running the available tools, rejecting misleading source geometry, and proving the achieved output quality.

The expected result is a clean, explainable deliverable: a repaired mesh, fitted profile data, STEP/BREP solid, optional tool-specific output, and validation evidence that matches the requested quality level.

## Activation Criteria

Invoke this skill when the task involves any of the following:

- reconstructing a curved or freeform part from STL, OBJ, PLY, XYZ, PTS, CSV, STEP, or tool-native CAD input;
- turning a mesh or point cloud into ordered profiles, fitted surfaces, STEP, STL preview, or CAD-ready output;
- rebuilding cushions, pillows, pads, ergonomic supports, handles, shells, curved blocks, or soft-body product geometry;
- separating a desired main body from straps, seams, stitches, labels, zippers, brackets, thin sheets, scan fragments, or other accessory geometry;
- validating watertightness, manifold state, positive volume, body count, face count, fit quality, or visual correspondence;
- deciding whether to deliver Q0 mesh repair, Q1 fitted profiles, Q2 single BREP solid, Q3 feature-native CAD, or Q4 verified native output.

Do not invoke this skill for ordinary 2D drafting, unrelated mechanical design, generic CAD questions, or copying protected commercial geometry without authorization.

## Safety And Authorization

Only reconstruct user-owned, user-supplied, or otherwise authorized geometry. If the input appears to be a commercial product, third-party model, branded component, or protected design and permission is unclear, ask the user to confirm authorization before reproducing the geometry in detail.

Preserve the original source file. Never overwrite the source. Put generated files in `_work/`, `work/`, or an explicit output directory.

## Inputs

Supported input categories:

- mesh: binary STL, ASCII STL where supported by the selected script, OBJ, ASCII PLY;
- point samples: XYZ, PTS, CSV, scanned point-cloud subsets;
- CAD/BREP: STEP or tool-native files through adapters, not through the simple core point-sampling route;
- design intent: target body, faces to preserve, concavity, desired section axis, tolerance, output format, editability requirements.

Before running reconstruction, clarify or infer:

- whether the target is visual fit, one solid body, or editable native features;
- whether accessories should be excluded or preserved;
- whether output should prioritize Q2 single-solid reliability or Q3/Q4 native editability;
- required unit scale and coordinate orientation when not obvious.

## Outputs

Possible outputs:

- geometry inspection report;
- component summary and contact sheet;
- included/excluded component list;
- profile/fit JSON;
- reconstructed surface or closed solid;
- STEP, preview STL, OBJ, PLY, or tool-native file through an adapter;
- validation report with topology, volume, body count, face count, and visual evidence.

Always state the achieved quality level. Do not imply that a STEP-imported SLDPRT is an editable native feature tree unless it was actually rebuilt with native sketches/features.

## Quality Levels

- **Q0 Mesh Repair**: cleaned mesh only; useful for preview or 3D printing; weak editability.
- **Q1 Fitted Surface / Profiles**: sampled or fitted target surface/profile data; useful for iteration and downstream CAD construction.
- **Q2 Single BREP Solid**: watertight/manifold-style closed solid with positive volume and STEP export; reliable for handoff but not necessarily parametric.
- **Q3 Tool-Native Feature Model**: editable sketches, splines, lofts, surfaces, cuts, planes, and named features in a target CAD system.
- **Q4 Verified Native Deliverable**: native file plus independent verification evidence proving the required body/face/topology state.

## Agent Operating Procedure

1. **Confirm scope and authorization**
   - Confirm ownership/permission if the source is commercial or third-party.
   - Preserve the raw input.
   - Identify desired output quality: Q0, Q1, Q2, Q3, or Q4.

2. **Inspect before fitting**
   - Run generic checks: bounding box, point/vertex/triangle count, open edges, nonmanifold edges, degenerate faces, signed volume, positive volume.
   - For multi-part STL/OBJ scenes, use `core/mesh_scene_inspector.py` before profile generation.
   - If a single STL/OBJ contains detached shells, run the inspector with `--split-components`.

3. **Choose the intended target body**
   - Treat source mesh as a scene until proven otherwise.
   - Identify the desired main body by design intent, connected size, thickness, curvature continuity, and visual review.
   - Reject straps, seams, stitches, labels, zippers, brackets, thin sheets, decorative strips, and scan fragments unless the user explicitly asks to reproduce them.
   - Record included and excluded mesh/body ids.

4. **Select reconstruction route**
   - Use core sampling/fitting for mesh or point inputs.
   - Use CadQuery/OCC or FreeCAD when a robust STEP/BREP solid is the priority.
   - Use SolidWorks only when Windows and a licensed SolidWorks installation are available.
   - Use native feature reconstruction only when the adapter actually creates sketches, splines, lofts, cuts, planes, and named features.

5. **Generate ordered sections or patches**
   - Choose the section axis from object design flow, not only bounding-box length.
   - Define coverage on the selected main body, not on the full scene including accessories.
   - Use consistent point order and section landmarks.
   - Use multiple spline edges when a section has concavity, side bulges, saddle curvature, asymmetric thickness, or non-elliptic contour.

6. **Build the deliverable**
   - For Q2, build closed profile wires and loft them into one BREP/STEP solid.
   - For Q3/Q4, create native CAD features rather than importing a STEP and calling it editable.
   - For Q0, explicitly label the result as mesh-only.

7. **Validate before completion**
   - Verify topology and validity appropriate to the output type.
   - Compare source and output in matching isometric, front, side, and top views.
   - Include a slice/profile preview or contact sheet for complex section-based reconstructions.
   - Confirm that excluded accessories were not fitted into the body.
   - Confirm that major target-body mass was not truncated.

8. **Report clearly**
   - State commands run, inputs used, outputs created, validation results, and known limitations.
   - If a fallback route was used, state why.
   - If the output is valid but visually questionable, do not claim success without qualification.

## Main-Body Fitting Rules

A curved product mesh often contains the main body plus straps, seams, trim, decorative surfaces, scan fragments, and separate support hardware. Do not fit everything visible just because it is in the file.

- Prefer the smooth load-bearing or visible product mass when the user asks for the primary body.
- Reject thin, long, detached, high-aspect-ratio, or low-volume-fill components unless requested.
- If a candidate changes the gross silhouette but is clearly a strap, back band, stitch, zipper, label, or decorative patch, exclude it from the main-body fit and document the exclusion.
- Do not merge separated components into one section envelope unless they are physically part of the desired single solid.
- For complex scenes, make a component contact sheet before deciding what to fit.

## Section And Spline Rules

Profile quality matters more than point count.

- Choose the section axis from object design flow and verify it visually.
- State whether coverage is bbox-based or quantile-based.
- Use real fitted sections as close to the object ends as possible.
- If side truncation appears, check section range before adding caps.
- Do not shrink several real end sections simply to make a rounded cap.
- Do not force sections into ellipses when the reference has concavity, side bulges, saddle curvature, or asymmetric thickness.
- Keep profile point order and section landmarks consistent across all sections to avoid twisted lofts.
- When exact slicing gives multiple loops, keep the largest main-body loop by default; keep smaller loops only when they are real holes or main-body features.

## End-Cap And Truncation Rules

Flat side faces are a warning sign, not merely a cosmetic problem.

- Extend and inspect the real section range before adding end caps.
- End caps should consume only the residual tail outside the validated main-body section range.
- If caps make the body thinner or less faithful than the uncapped version, preserve the best real-section loft and report the remaining side flatness.
- Fillet only the intended end edges when possible. Do not blindly fillet every loft edge.

## Core Versus Adapters

Core work is tool-independent:

- read supported mesh/point inputs;
- inspect topology and scale;
- segment main body versus accessories;
- sample target surfaces or sections;
- fit polynomial/spline profiles;
- emit profile JSON and validation reports.

Adapters connect core data to CAD tools:

- `adapters/cadquery`: CadQuery/OCC BREP loft and STEP/STL export.
- `adapters/freecad`: FreeCAD scripting route for open-source CAD workflows.
- `adapters/occt`: direct OpenCascade concepts and future low-level hooks.
- `adapters/solidworks`: optional Windows/SolidWorks import/export/verification route.

Current SolidWorks adapter limitation: importing STEP and saving SLDPRT is not the same as rebuilding a native editable SolidWorks feature tree. Only claim Q3/Q4 native feature output if sketches, splines, planes, lofts, cuts, and named features were actually created in SolidWorks or another target CAD system.

## Stop Conditions

Stop only when the required quality level is proven by current evidence.

For a complete solid, require at minimum:

- valid BREP or watertight/manifold mesh state where applicable;
- positive volume;
- one solid body if the task requires a single solid;
- no known self-intersection or invalid geometry status;
- approximation or fit error within the stated tolerance, or an explicit statement that the result is visual-fit only;
- exported file exists and reopens in the target adapter when requested.

For a native CAD deliverable, also require:

- target CAD file created successfully;
- reopened-file verification;
- body count and face count reported;
- feature-native construction evidence if editability was requested.

## Resources

- Read `docs/workflow.md` for the full tool-agnostic process.
- Read `docs/environment.md` for dependency and adapter requirements.
- Read `docs/commands.md` for relative command templates.
- Use `core/mesh_scene_inspector.py` before fitting multi-part or detailed STL/OBJ inputs.
- Use `core/verify_geometry.py` before reconstruction.
- Use `core/surface_profiles_from_samples.py` to create simple height-field-style profile JSON.
- Use adapters only after core profile/validation evidence is clear.
- See `examples/cases/m1009` for a compact single-solid route.
- See `examples/cases/h3-audi-headrest` for a multi-part soft-cushion case showing main-body filtering, multi-spline section fitting, section coverage pitfalls, and end-cap/truncation lessons.
