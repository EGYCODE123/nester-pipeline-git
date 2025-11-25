# Development run script for Waste API
$ErrorActionPreference = "Stop"
Set-Location "Z:\CPQ Waste\nester-pipeline"

if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    py -m venv .venv
}

Write-Host "Installing dependencies..."
.\.venv\Scripts\pip install -r requirements.txt

Write-Host "Starting API server..."
Write-Host "API will be available at http://localhost:8000"
Write-Host "Press Ctrl+C to stop"
.\.venv\Scripts\uvicorn nester_api.app.main:app --host 0.0.0.0 --port 8000 --reload

            