$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$case = Join-Path $root "examples\cases\m1009"
$work = Join-Path $case "_work"
New-Item -ItemType Directory -Path $work -Force | Out-Null

$inputStl = Join-Path $case "input\M1009_curved_face_block_reference.STL"
$geometryReport = Join-Path $work "geometry_report.json"
$profiles = Join-Path $work "profiles.json"
$step = Join-Path $work "single_solid.step"
$preview = Join-Path $work "single_solid_preview.stl"

python (Join-Path $root "core\verify_geometry.py") $inputStl --out $geometryReport
python (Join-Path $root "core\surface_profiles_from_samples.py") $inputStl --out $profiles --sections 20 --points 7 --drop-section 11
python (Join-Path $root "adapters\cadquery\single_solid_from_profiles.py") $profiles --step $step --preview-stl $preview

if (-not (Test-Path $step)) {
    throw "Missing STEP output: $step"
}
if (-not (Test-Path $preview)) {
    throw "Missing STL preview output: $preview"
}

Write-Output "SMOKE_TEST_OK"
