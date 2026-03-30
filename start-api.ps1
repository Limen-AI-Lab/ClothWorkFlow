# Start ClothWorkFlow API + static frontend (port 8000).
# Default: auto-loads the first dataset from /api/analysis-dirs (same as python -m clothworkflow.api).
# To skip startup load: $env:CLOTHWORKFLOW_AUTO_LOAD = "0"
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Missing .venv. From project root run: python -m venv .venv; .\.venv\Scripts\pip install -e ."
}
& $py -m clothworkflow.api
