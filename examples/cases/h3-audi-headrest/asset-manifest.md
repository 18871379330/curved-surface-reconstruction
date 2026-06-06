# Asset Manifest

## Input

- `input/quersus_h3_audi_cushion_shell_only.stl`  
  Curated cushion-shell reference used for spline fitting. Accessory strap/ribbon/seam-loop meshes were removed before this reference was created.

- `input/poduszka_zaglowkowa_audi_mesh_summary.tsv`  
  Mesh candidate summary from the original FBX extraction.

- `input/poduszka_zaglowkowa_audi_candidate_contact_sheet.png`  
  Visual contact sheet for component classification.

- `input/h3_candidate_mesh_scene_report.json`  
  General scene-inspector JSON report for the extracted H3 mesh candidates.

- `input/h3_candidate_mesh_scene_summary.tsv`  
  General scene-inspector TSV summary for the extracted H3 mesh candidates.

- `input/h3_candidate_mesh_scene_contact_sheet.png`  
  General scene-inspector contact sheet for the extracted H3 mesh candidates.

- `input/h3_full_headrest_split_scene_report.json`  
  Connected-shell scene-inspector JSON report from the single full-headrest STL.

- `input/h3_full_headrest_split_scene_summary.tsv`  
  Connected-shell scene-inspector TSV summary from the single full-headrest STL.

- `input/h3_full_headrest_split_contact_sheet.png`  
  Connected-shell scene-inspector contact sheet from the single full-headrest STL.

## Code

- `case-code/build_h3_audi_spline_pillow.py`  
  Final retained case script. It fits ordered left-to-right sections with multiple spline edges per closed section wire.

- `case-code/render_h3_audi_comparison.py`  
  Utility for visual source/output comparison.

## Profiles

- `profiles/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid_profiles.json`  
  Retained extended-section profile data and reconstruction parameters.

- `profiles/h3_audi_spline_fitted_pillow_single_solid_profiles.json`  
  Best visual baseline profile data kept for comparison.

## Outputs

- `outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid.SLDPRT`  
  Retained SolidWorks part.

- `outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid.step`  
  Retained STEP output.

- `outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid_preview.png`  
  Retained preview image.

- `outputs/h3_audi_spline_fitted_extended_real_sections_pillow_single_solid_validation.json`  
  CadQuery/STEP validation report.

- `outputs/h3_audi_spline_fitted_pillow_single_solid_baseline.SLDPRT`  
  Best visual baseline SolidWorks part.

- `outputs/h3_audi_spline_fitted_pillow_single_solid_baseline.step`  
  Best visual baseline STEP output.

- `outputs/h3_audi_spline_fitted_pillow_single_solid_baseline_preview.png`  
  Best visual baseline preview image.

## Notes

This case intentionally keeps both the retained extended-section output and the best baseline. The baseline is valuable because later iterations showed that more aggressive full-range fitting can include unwanted accessory geometry and make the reconstruction worse.
