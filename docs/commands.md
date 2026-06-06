# Relative Command Templates

Run commands from the skill folder unless otherwise noted.

## Core Geometry Verification

```powershell
python core\verify_geometry.py examples\cases\m1009\input\M1009_curved_face_block_reference.STL --out examples\cases\m1009\_work\geometry_report.json
```

Expected checks for a closed mesh:

```text
watertight: true
manifold: true
positive_volume: true
```

## Inspect Mesh Scene And Components

Use this before profile generation when an STL/OBJ may contain multiple bodies, straps, seams, ribbons, thin sheets, or decorative fragments. Directory inspection prefers same-stem STL over OBJ by default to avoid double-counting exported format pairs.

```powershell
python core\mesh_scene_inspector.py path\to\mesh_or_directory `
  --out-json path\to\_work\mesh_scene_report.json `
  --out-tsv path\to\_work\mesh_scene_summary.tsv `
  --contact-sheet path\to\_work\mesh_scene_contact_sheet.png
```

For one STL/OBJ that contains many detached shells:

```powershell
python core\mesh_scene_inspector.py path\to\full_scene.stl `
  --split-components `
  --out-json path\to\_work\split_scene_report.json `
  --out-tsv path\to\_work\split_scene_summary.tsv `
  --contact-sheet path\to\_work\split_scene_contact_sheet.png
```

Use `classification`, `main_body_score`, `recommendation`, `classification_reasons`, `risk_notes`, and the contact sheet together. The labels are advisory; final inclusion must follow the user's design intent.

## Generate Profiles

```powershell
python core\surface_profiles_from_samples.py examples\cases\m1009\input\M1009_curved_face_block_reference.STL `
  --out examples\cases\m1009\_work\profiles.json `
  --sections 20 `
  --points 7 `
  --drop-section 11
```

Before generating profiles for a multi-part or detailed product mesh, complete this manual checklist:

```text
1. Mesh/component summary exists.
2. Included main-body mesh ids are recorded.
3. Excluded accessory/detail mesh ids are recorded.
4. Section axis is chosen from design intent, not only bbox size.
5. Coverage is stated as bbox-based or quantile-based.
6. Representative section/profile preview is planned.
7. End caps are limited to the residual tail after real sections cover the target body.
```

If a model contains straps, seams, stitches, zippers, labels, brackets, thin sheets, or decorative patches, do not let those parts define the main-body profile envelope unless the user explicitly requests them.

## Build Single BREP/STEP With CadQuery

```powershell
python adapters\cadquery\single_solid_from_profiles.py examples\cases\m1009\_work\profiles.json `
  --step examples\cases\m1009\_work\single_solid.step `
  --preview-stl examples\cases\m1009\_work\single_solid_preview.stl
```

Expected evidence:

```text
VALID True
FACES 6
SOLIDS 1
```

## Optional SolidWorks Import

Compile the SolidWorks adapter into a private work directory that also contains local SolidWorks interop DLLs.

```powershell
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo `
  /r:path\to\SolidWorks.Interop.sldworks.dll `
  /r:path\to\SolidWorks.Interop.swconst.dll `
  /out:examples\cases\m1009\_work\solidworks_import_step_verify.exe `
  adapters\solidworks\import_step_verify.cs
```

Then run:

```powershell
& examples\cases\m1009\_work\solidworks_import_step_verify.exe `
  examples\cases\m1009\_work\single_solid.step `
  examples\cases\m1009\_work\single_solid.SLDPRT `
  examples\cases\m1009\_work\single_solid_preview.png
```

## Optional SolidWorks Reopen Verification

```powershell
& C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo `
  /r:path\to\SolidWorks.Interop.sldworks.dll `
  /r:path\to\SolidWorks.Interop.swconst.dll `
  /out:examples\cases\m1009\_work\verify_sldprt_single_solid.exe `
  adapters\solidworks\verify_sldprt_single_solid.cs

& examples\cases\m1009\_work\verify_sldprt_single_solid.exe examples\cases\m1009\_work\single_solid.SLDPRT
```

Expected evidence:

```text
FINAL_SOLID_BODIES=1
VERIFIED_SINGLE_SOLID=True
```
