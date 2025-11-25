# Script to create a strong name key file for signing the assembly
$ErrorActionPreference = "Stop"

$snkPath = "Kvadrat.NesterBridge\Kvadrat.NesterBridge.snk"

if (Test-Path $snkPath) {
    Write-Host "Strong name key file already exists: $snkPath" -ForegroundColor Yellow
    $response = Read-Host "Do you want to overwrite it? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Cancelled" -ForegroundColor Gray
        exit 0
    }
}

# Find sn.exe
$snExe = $null
$snPaths = @(
    "${env:ProgramFiles(x86)}\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\sn.exe",
    "${env:ProgramFiles}\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\sn.exe",
    "${env:ProgramFiles(x86)}\Microsoft SDKs\Windows\v8.1A\bin\NETFX 4.5.1 Tools\sn.exe"
)

foreach ($path in $snPaths) {
    if (Test-Path $path) {
        $snExe = $path
        break
    }
}

if (-not $snExe) {
    Write-Host "ERROR: sn.exe (Strong Name Tool) not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Visual Studio Build Tools or Windows SDK" -ForegroundColor Yellow
    Write-Host "Download: https://visualstudio.microsoft.com/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Alternatively, you can create the key file manually:" -ForegroundColor Yellow
    Write-Host "  sn -k `"$snkPath`"" -ForegroundColor White
    exit 1
}

Write-Host "Creating strong name key file..." -ForegroundColor Yellow
Write-Host "Using: $snExe" -ForegroundColor Gray

& $snExe -k "`"$snkPath`""

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Strong name key file created successfully: $snkPath" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to create strong name key file" -ForegroundColor Red
    Write-Host "You may need to run this script as Administrator" -ForegroundColor Yellow
    exit 1
}



