# Environment Matrix

## Core Python

Use for mesh/point inspection, sampling, fitting, and profile JSON generation.

Requirements:

```text
numpy
```

Optional:

```text
scipy
```

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
4. SolidWorks only as an optional Windows export/verification adapter.
