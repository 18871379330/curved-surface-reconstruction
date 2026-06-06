---
name: curved-surface-reconstruction
description: Tool-agnostic framework for reconstructing curved surfaces and closed solids from STL, OBJ, PLY, STEP, and point-cloud inputs. Use when Codex needs to sample, fit, repair, reverse-model, validate, or export freeform product geometry with adapters for CadQuery/OpenCascade, FreeCAD, SolidWorks, or mesh repair pipelines, including cases requiring watertight/manifold solids, BREP/STEP output, or validation reports.
---

# Curved Surface Reconstruction

## Scope

Reconstruct user-owned or authorized curved geometry into a verified output. Accept mesh, CAD, or point-sample inputs; produce a fit report, reconstructed surface/solid, export files, and validation evidence.

Do not use this skill to copy protected commercial geometry without authorization. If ownership or permission is unclear, ask for confirmation before reproducing detailed geometry.

## Inputs And Outputs

Inputs:

- mesh: STL, OBJ, PLY;
- CAD/BREP: STEP or tool-native parts through adapters;
- point samples: XYZ, PTS, CSV, scanned point cloud subsets;
- optional design intent: preserved faces, target concavity, tolerance, desired output format.

Outputs:

- profile/fit JSON;
- reconstructed surface or closed solid;
- neutral export such as STEP, STL preview, OBJ, or PLY;
- optional tool-native output through adapters;
- validation report with topology, volume, and approximation checks.

## Quality Levels

- **Q0 Mesh Repair**: cleaned mesh only; useful for preview or 3D printing, weak editability.
- **Q1 Fitted Surface**: sampled/fitted target surface with profile data; useful for design iteration.
- **Q2 Single BREP Solid**: watertight/manifold closed solid, positive volume, exportable STEP.
- **Q3 Tool-Native Feature Model**: editable sketches/splines/lofts in a target CAD system; best editability but may be harder to keep as one body.
- **Q4 Verified Native Deliverable**: target tool file plus independent verification report proving the requested body/face/topology state.

## Decision Tree

1. Confirm authorization and preserve the source file.
2. Normalize input units and coordinate frame.
3. Run generic geometry checks: bounding box, point/face count, watertight, manifold, volume.
4. Segment the source into design-relevant components before fitting:
   - use `core/mesh_scene_inspector.py` for STL/OBJ scenes, directories, and single files that may contain many connected shells;
   - identify the primary body or target surface that the user actually wants;
   - exclude straps, seams, stitches, labels, zippers, ribs, brackets, thin sheets, and other detail geometry unless the user explicitly asks to reproduce them;
   - record included and excluded mesh/body ids in the fit report.
5. Select reconstruction target:
   - use core sampling/fitting for mesh or point data;
   - use a CAD adapter for STEP/native body extraction;
   - use mesh repair if the input is too noisy for fitting.
6. Generate ordered profiles or surface patches from the target body, not from the whole scene.
7. Build the best output:
   - feature-native reconstruction when editability is primary;
   - BREP/STEP reconstruction when one complete solid is primary;
   - repaired mesh when only concept/print preview is feasible.
8. Validate against the requested quality level before claiming completion.

## Main-Body Fitting Rules

Treat an STL/OBJ file as a scene until proven otherwise. A curved product mesh often contains the main soft body plus accessory parts, seams, straps, decorative surfaces, and texture-derived fragments. Do not fit all visible geometry just because it is present.

- First choose the target body by design intent, connected size, thickness, curvature continuity, and user wording.
- Prefer fitting the smooth load-bearing or visible product mass; reject thin, long, detached, or high-aspect-ratio accessory pieces unless requested.
- If the model is split into many mesh nodes, make a mesh summary and visual contact sheet before reconstruction.
- If a candidate component changes the gross silhouette but is clearly a strap, back band, stitch, zipper, label, or decorative patch, keep it out of the main body fit and document the exclusion.
- Do not merge separated components into one section envelope unless they are physically part of the desired single solid.

## Section And Spline Rules

For freeform solids, profile quality matters more than point count.

- Choose the section axis from the object's design flow and verify it visually. For pillows, pads, handles, shells, and ergonomic surfaces, the best axis is often left-to-right or end-to-end.
- Coverage targets, such as 99%, apply to the selected main body on that axis, not to the raw scene including accessory pieces.
- Report whether coverage is based on bbox span or point quantiles. These can differ strongly near tapered ends.
- If the side view shows a flat cut, do not assume the end cap is the problem first; check whether the real section range stopped too early.
- Use real fitted sections as close to the object ends as possible. Only the remaining tail should be rounded, capped, or filleted.
- Do not force every section into an ellipse or simple envelope when the reference has concavity, side bulges, saddle curvature, or asymmetric thickness.
- A section may need multiple spline edges. Use as many spline segments as needed to capture the stable outer contour.
- If exact slicing produces multiple closed loops, keep the largest main-body loop by default. Include smaller loops only when they are true holes or main-body features, not straps or detached details.
- Keep profile point order and section landmarks consistent across all sections to avoid twisted lofts.

## End-Cap And Truncation Rules

Flat side faces are a warning sign, not a cosmetic issue.

- First extend the real section range and inspect slice coverage before adding end caps.
- Do not shrink several real end sections just to make a rounded cap; that can discard visible mass and make the part less faithful.
- End caps should only consume the small remainder outside the validated main-body section range.
- If the CAD kernel cannot fillet end edges reliably, preserve the best real-section loft and report the residual flatness rather than distorting the body with artificial caps.
- Validate side, front, top, and isometric views after any cap or fillet change.

## Visual Validation Rules

Single-solid validation is necessary but not sufficient.

- Compare source and output in identical views: isometric, front, side, and top.
- Include a slice-profile preview or contact sheet for complex section-based reconstructions.
- Check that the result did not fit excluded accessories and did not omit major main-body mass.
- If a later iteration looks worse than an earlier one, return to the best previous method and make the smallest correction needed.

## Core Versus Adapters

Core does tool-independent work:

- read mesh/point inputs;
- segment target body versus accessory components;
- sample target surfaces;
- fit polynomial/spline profiles;
- emit profile JSON;
- compute generic geometry checks.

Adapters connect core data to tools:

- `adapters/cadquery`: CadQuery/OCC BREP loft and STEP/STL export.
- `adapters/freecad`: FreeCAD scripting route for open-source CAD.
- `adapters/occt`: direct OpenCascade concepts and future low-level hooks.
- `adapters/solidworks`: optional Windows/SolidWorks API route for SLDPRT import/export/verification.

## Stop Conditions

Stop only when the required quality level is proven by current evidence. For a complete solid, require at minimum:

- watertight/manifold where applicable;
- positive volume;
- no known self-intersection or invalid BREP status;
- approximation/fit error within the stated tolerance or explicitly reported;
- exported file exists and reopens in the target adapter when requested.

## Resources

- Read `docs/workflow.md` for the full tool-agnostic process.
- Read `docs/environment.md` for the Python-first environment matrix.
- Read `docs/commands.md` for relative command templates.
- Use `core/mesh_scene_inspector.py` before fitting multi-part or detailed STL/OBJ inputs.
- Use `core/verify_geometry.py` before reconstruction.
- Use `core/surface_profiles_from_samples.py` to create profile JSON.
- Use adapters only after the core profile/validation stage is clear.
- See `examples/cases/m1009` as a private/self-owned case demonstration, not as the global workflow.
- See `examples/cases/h3-audi-headrest` for a multi-part soft cushion case showing main-body filtering, multi-spline section fitting, section coverage pitfalls, and end-cap/truncation lessons.
