# Case M1009

This is a private/self-owned demonstration case for the curved-surface reconstruction framework.

## Route

```text
reference STL
-> generic geometry verification
-> target-face surface sampling
-> fitted section profiles
-> CadQuery/OCC single BREP solid
-> STEP
-> optional SolidWorks SLDPRT import/verification
```

## Key Evidence From The Original Run

Mesh inspection:

```text
triangles: 53996
vertices: 27000
open_edges: 0
nonmanifold_edges: 0
degenerate_faces: 0
```

CadQuery/OCC BREP:

```text
VALID True
VOLUME_MM3 4326180.577801475
FACES 6
SOLIDS 1
```

Optional SolidWorks verification:

```text
FINAL_SOLID_BODIES=1
FINAL_FACE_COUNT=6
FINAL_PLANE_FACES=2
FINAL_NONPLANE_FACES=4
VERIFIED_SINGLE_SOLID=True
```

## Files

- `input/M1009_curved_face_block_reference.STL`: source mesh used for fitting.
- `profiles/native_loft_profiles.json`: fitted profiles from the original case run.
- `outputs/M1009_curved_face_block_single_solid.step`: single-solid STEP.
- `outputs/M1009_curved_face_block_single_solid_preview.stl`: preview STL.
- `outputs/M1009_curved_face_block_complete_single_solid.SLDPRT`: optional SolidWorks final file from the original local run.
- `outputs/M1009_curved_face_block_complete_single_solid_preview.png`: visual preview.
- `case-code/`: original case-specific scripts retained as teaching material.
