param([string]$Config="Release")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
cd "$root\.."

Write-Host "=== Building Kvadrat.NesterBridge for Release ===" -ForegroundColor Cyan

# Find MSBuild
$msbuild = $null
$msbuildPaths = @(
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe"
)

foreach ($path in $msbuildPaths) {
    if (Test-Path $path) {
        $msbuild = $path
        break
    }
}

if (-not $msbuild) {
    Write-Error "MSBuild not found. Please install Visual Studio Build Tools."
    exit 1
}

Write-Host "Using MSBuild: $msbuild" -ForegroundColor Gray

# Restore packages if nuget.exe exists
$nugetPath = Join-Path $root "..\nuget.exe"
if (Test-Path $nugetPath) {
    Write-Host "`nRestoring NuGet packages..." -ForegroundColor Yellow
    Push-Location (Join-Path $root "..\Kvadrat.NesterBridge")
    & $nugetPath restore packages.config -PackagesDirectory ..\packages
    Pop-Location
} else {
    Write-Host "`nSkipping NuGet restore (nuget.exe not found, MSBuild will restore automatically)" -ForegroundColor Yellow
}

# Build
Write-Host "`nBuilding Kvadrat.NesterBridge ($Config, AnyCPU)..." -ForegroundColor Yellow
& $msbuild "Kvadrat.NesterBridge\Kvadrat.NesterBridge.csproj" /p:Configuration=$Config /p:Platform=AnyCPU /t:Clean,Build /verbosity:minimal

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}

# Locate output DLL (from the actual project, not test project)
$dll = Get-ChildItem -Recurse -Filter "Kvadrat.NesterBridge.dll" | Where-Object { 
    $_.FullName -match "\\Kvadrat\.NesterBridge\\bin\\$Config\\" -and 
    $_.FullName -notmatch "BridgeConsoleTest"
} | Select-Object -First 1

if (-not $dll) {
    throw "DLL not found after build"
}

Write-Host "`nFound DLL: $($dll.FullName)" -ForegroundColor Green

# Copy Newtonsoft.Json.dll if local package is used
$pkgDll = Get-ChildItem -Recurse -Filter "Newtonsoft.Json.dll" | Where-Object { $_.FullName -match "\\packages\\Newtonsoft.Json" } | Select-Object -First 1

# Extract version from AssemblyInfo.cs
$assemblyInfoPath = "Kvadrat.NesterBridge\Properties\AssemblyInfo.cs"
$versionMatch = Select-String -Path $assemblyInfoPath -Pattern 'AssemblyFileVersion\("([^"]+)"\)'
if ($versionMatch) {
    $ver = $versionMatch.Matches[0].Groups[1].Value
} else {
    $ver = "1.0.2.0"
    Write-Warning "Could not extract version, using default: $ver"
}

# Create dist folder with version
$dist = "dist\Kvadrat.NesterBridge_$ver"
New-Item -ItemType Directory -Force -Path $dist | Out-Null

# Copy DLLs
Copy-Item $dll.FullName $dist -Force
Write-Host "Copied: $($dll.Name)" -ForegroundColor Gray

if ($pkgDll) {
    Copy-Item $pkgDll.FullName $dist -Force
    Write-Host "Copied: $($pkgDll.Name)" -ForegroundColor Gray
} else {
    Write-Warning "Newtonsoft.Json.dll not found in packages folder"
}

# Copy README
$readmeSource = "dist\README_Experlogix.txt"
if (Test-Path $readmeSource) {
    Copy-Item $readmeSource $dist -Force
    Write-Host "Copied: README_Experlogix.txt" -ForegroundColor Gray
}

Write-Host "`n=== Build Complete ===" -ForegroundColor Green
Write-Host "Output directory: $dist" -ForegroundColor Cyan
Write-Host "`nFiles:" -ForegroundColor Cyan
Get-ChildItem $dist | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }

