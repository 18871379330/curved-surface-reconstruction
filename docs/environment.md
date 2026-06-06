# Environment Matrix

## Core Python

Use for mesh/point inspection, sampling, fitting, profile JSON generation, component contact sheets, and lightweight validation.

Requirements:

```text
numpy
pillow
```

`pillow` is required by `core/mesh_scene_inspector.py` and the H3 preview renderer for contact-sheet and preview-image generation.

Optional:

```text
scipy
pytest
```

`scipy` is useful for future fitting and interpolation routes. `pytest` is recommended for local smoke tests.

## CadQuery Adapter

Use for single BREP solid generation and STEP/STL export.

Requirements:

```text
cadquery
```

CadQuery bundles an OCC/OpenCascade runtime. This is the preferred Python-first route for single-solid output.

## FreeCAD Adapter

Use when an open-source CAD GUI or scripting environment is preferred.

Requirements:

- FreeCAD installed;
- `FreeCADCmd` available on PATH, or explicit executable path.

## OCCT Adapter

Use for lower-level OpenCascade work when direct control over sewing, healing, or BREP construction is needed.

Requirements vary by binding:

- CadQuery/OCP;
- pythonocc-core;
- native C++ OCCT.

## SolidWorks Adapter

Use only when a Windows machine has SolidWorks installed and the output must be SLDPRT or SolidWorks-verified.

Current adapter scope:

- import STEP into SolidWorks;
- save the imported model as SLDPRT;
- reopen or inspect the resulting part;
- verify solid-body count, face count, and basic face-type statistics.

Current adapter non-scope:

- rebuilding editable SolidWorks feature trees;
- creating native sketches, splines, lofts, cuts, named planes, or design-table parameters;
- guaranteeing parametric editability after STEP import.

Requirements:

- SolidWorks installed and licensed;
- Windows;
- .NET Framework compiler such as `csc.exe`;
- local `SolidWorks.Interop.sldworks.dll` and `SolidWorks.Interop.swconst.dll`.

Do not bundle proprietary SolidWorks interop DLLs in a public skill/repository. Locate them from the local SolidWorks installation or copy them into a private adapter working directory when testing.

## Recommended Priority

1. Core Python.
2. CadQuery/OCC for BREP/STEP.
3. FreeCAD for open-source CAD workflows.
4. SolidWorks only as an optional Windows import/export/verification adapter.
