# Install Windows Service for Kvadrat Waste API using NSSM
param(
    [string]$ServiceName = "KvadratWasteAPI",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = "Z:\CPQ Waste\nester-pipeline"

if (-not (Test-Path "$root\.venv\Scripts\uvicorn.exe")) {
    Write-Error "Virtual environment not found. Please run scripts/dev_run.ps1 first to create it."
    exit 1
}

if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) {
    Write-Error "NSSM is not installed. Please download from https://nssm.cc/download and add to PATH."
    exit 1
}

$exe = "$root\.venv\Scripts\uvicorn.exe"
$args = "nester.api.app:app --host 0.0.0.0 --port $Port"

Write-Host "Installing service: $ServiceName"
nssm install $ServiceName $exe $args

Write-Host "Configuring service..."
nssm set $ServiceName AppDirectory $root

# Extract API_TOKEN from .env file
if (Test-Path "$root\.env") {
    $envContent = Get-Content "$root\.env" | Select-String '^API_TOKEN='
    if ($envContent) {
        $token = $envContent.ToString().Split('=')[1]
        nssm set $ServiceName AppEnvironmentExtra "API_TOKEN=$token"
        Write-Host "API_TOKEN configured from .env"
    }
}

nssm set $ServiceName Start SERVICE_AUTO_START
nssm set $ServiceName AppStdout "$root\logs\service_out.log"
nssm set $ServiceName AppStderr "$root\logs\service_err.log"

Write-Host ""
Write-Host "Service '$ServiceName' installed successfully!"
Write-Host "To start the service, run: nssm start $ServiceName"
Write-Host "To stop the service, run: nssm stop $ServiceName"
Write-Host "Service logs will be written to: $root\logs\"









