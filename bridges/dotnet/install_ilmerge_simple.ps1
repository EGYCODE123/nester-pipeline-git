# Simple script to install ILMerge via NuGet
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot"

Write-Host "=== Installing ILMerge ===" -ForegroundColor Cyan

# Check for NuGet.exe
$nugetExe = $null
$nugetPaths = @(
    "nuget.exe",
    "${env:ProgramFiles(x86)}\NuGet\nuget.exe",
    "${env:ProgramFiles}\NuGet\nuget.exe"
)

foreach ($path in $nugetPaths) {
    if (Test-Path $path) {
        $nugetExe = $path
        break
    }
}

# Download NuGet.exe if not found
if (-not $nugetExe) {
    Write-Host "NuGet.exe not found. Downloading..." -ForegroundColor Yellow
    try {
        $nugetUrl = "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe"
        Invoke-WebRequest -Uri $nugetUrl -OutFile "nuget.exe" -UseBasicParsing -ErrorAction Stop
        $nugetExe = "nuget.exe"
        Write-Host "NuGet.exe downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Error "Failed to download NuGet.exe: $_"
        Write-Host "`nPlease download NuGet.exe manually from:" -ForegroundColor Yellow
        Write-Host "https://www.nuget.org/downloads" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host "Using NuGet: $nugetExe" -ForegroundColor Gray

# Create tools directory
New-Item -ItemType Directory -Path "tools" -Force | Out-Null

# Install ILMerge
Write-Host "`nInstalling ILMerge package..." -ForegroundColor Yellow
& $nugetExe install ilmerge -OutputDirectory tools -Version 3.0.41

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install ILMerge package"
    exit 1
}

# Find and copy ILMerge.exe
$ilmergeSource = $null
$possiblePaths = @(
    "tools\ilmerge\tools\net452\ILMerge.exe",
    "tools\ilmerge\tools\ILMerge.exe",
    "tools\ilmerge.3.0.41\tools\ILMerge.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $ilmergeSource = $path
        break
    }
}

if (-not $ilmergeSource) {
    Write-Warning "ILMerge.exe not found in expected locations"
    Write-Host "Please check: tools\ilmerge\" -ForegroundColor Yellow
    exit 1
}

# Copy to tools\ILMerge.exe
Copy-Item $ilmergeSource -Destination "tools\ILMerge.exe" -Force
Write-Host "`n✅ ILMerge installed successfully!" -ForegroundColor Green
Write-Host "Location: tools\ILMerge.exe" -ForegroundColor Cyan

# Verify
if (Test-Path "tools\ILMerge.exe") {
    $fileInfo = Get-Item "tools\ILMerge.exe"
    Write-Host "`nFile size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB" -ForegroundColor Gray
    Write-Host "`nReady to build with ILMerge!" -ForegroundColor Green
} else {
    Write-Error "ILMerge.exe was not copied successfully"
    exit 1
}



