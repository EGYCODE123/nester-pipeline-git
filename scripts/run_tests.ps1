# Run pytest tests for Waste API
$ErrorActionPreference = "Stop"
Set-Location "Z:\CPQ Waste\nester-pipeline"

Write-Host "Installing dependencies..."
.\.venv\Scripts\pip install -r requirements.txt

Write-Host "Running tests..."
.\.venv\Scripts\pytest nester_api/tests/ -v







