# CadQuery Adapter

Use CadQuery/OCC to convert profile JSON into a single BREP solid and export STEP/STL.

Best for:

- Python-first workflows;
- single-solid BREP output;
- STEP export without relying on proprietary CAD software.

Main script:

- `single_solid_from_profiles.py`

Expected validation:

- `VALID True`;
- `SOLIDS 1`;
- volume > 0;
- face count is small and plausible.
