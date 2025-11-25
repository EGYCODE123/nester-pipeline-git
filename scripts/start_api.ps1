# Start API Server Script
$ErrorActionPreference = "Stop"
Set-Location "Z:\CPQ Waste\nester-pipeline"

Write-Host "=== Kvadrat Waste API ===" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    py -m venv .venv
}

# Install dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\pip install -q -r requirements.txt

Write-Host ""
Write-Host "Starting API server..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "📍 API URL:     http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 Swagger UI:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "📚 ReDoc:       http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host "🏥 Health Live: http://localhost:8000/health/live" -ForegroundColor Cyan
Write-Host "🏥 Health Ready: http://localhost:8000/health/ready" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
.\.venv\Scripts\uvicorn nester_api.app.main:app --host 0.0.0.0 --port 8000 --reload

