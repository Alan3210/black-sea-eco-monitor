AIR-COMMIT-CLEANUP v0.1

Purpose:
Prepare AIR-1.3 backend pipeline for clean git commit.

Actions:
- remove local test response air_field_response.json
- ignore AIR runtime cache
- ignore generated NetCDF inspection output

Does not modify:
- backend code
- frontend code
- API
- MapLibre layers

After running:
  git status --short

Then:
  git add .
  git commit -m "Add CAMS air quality backend pipeline"
  git push origin main
