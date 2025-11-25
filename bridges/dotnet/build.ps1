# Build script for Kvadrat.NesterBridge DLL and BridgeConsoleTest
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot"

Write-Host "=== Building Kvadrat.NesterBridge ===" -ForegroundColor Cyan

# Try to find MSBuild in various locations
$msbuild = $null
$msbuildPaths = @(
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\MSBuild\14.0\Bin\MSBuild.exe",
    "${env:ProgramFiles}\MSBuild\14.0\Bin\MSBuild.exe"
)

foreach ($path in $msbuildPaths) {
    if (Test-Path $path) {
        $msbuild = $path
        break
    }
}

# Try to find MSBuild via vswhere (Visual Studio Installer)
if (-not $msbuild) {
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -requires Microsoft.Component.MSBuild -find MSBuild\**\Bin\MSBuild.exe | Select-Object -First 1
        if ($vsPath -and (Test-Path $vsPath)) {
            $msbuild = $vsPath
        }
    }
}

# Check if dotnet CLI is available as fallback
$useDotnet = $false
if (-not $msbuild) {
    $dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
    if ($dotnet) {
        Write-Host "MSBuild not found, using dotnet CLI as fallback..." -ForegroundColor Yellow
        $useDotnet = $true
    }
}

if (-not $msbuild -and -not $useDotnet) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "ERROR: MSBuild not found" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Visual Studio CODE (VS Code) is installed, but it does NOT include build tools." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You need to install ONE of the following:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1: Visual Studio Build Tools (RECOMMENDED - Free, smaller download)" -ForegroundColor Green
    Write-Host "  Download: https://visualstudio.microsoft.com/downloads/" -ForegroundColor White
    Write-Host "  Select: 'Build Tools for Visual Studio 2022'" -ForegroundColor White
    Write-Host "  During installation, select: '.NET desktop build tools' workload" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2: Visual Studio Community (Free, full IDE)" -ForegroundColor Green
    Write-Host "  Download: https://visualstudio.microsoft.com/vs/community/" -ForegroundColor White
    Write-Host "  During installation, select: '.NET desktop development' workload" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 3: .NET SDK (Alternative - may work for some projects)" -ForegroundColor Green
    Write-Host "  Download: https://dotnet.microsoft.com/download" -ForegroundColor White
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Error "Build tools not found. Please install Visual Studio Build Tools or Visual Studio."
    exit 1
}

if ($msbuild) {
    Write-Host "Using MSBuild: $msbuild" -ForegroundColor Gray
}

if ($useDotnet) {
    # Use dotnet CLI for restore and build
    Write-Host "`nRestoring packages with dotnet..." -ForegroundColor Yellow
    & dotnet restore "Kvadrat.NesterBridge\Kvadrat.NesterBridge.csproj"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Restore failed for Kvadrat.NesterBridge"
        exit 1
    }
    
    Write-Host "`nBuilding Kvadrat.NesterBridge (Release)..." -ForegroundColor Yellow
    & dotnet build "Kvadrat.NesterBridge\Kvadrat.NesterBridge.csproj" -c Release --no-restore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed for Kvadrat.NesterBridge"
        exit 1
    }
    
    Write-Host "`nBuilding BridgeConsoleTest (Release)..." -ForegroundColor Yellow
    & dotnet build "BridgeConsoleTest\BridgeConsoleTest.csproj" -c Release --no-restore
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed for BridgeConsoleTest"
        exit 1
    }
} else {
    # Use MSBuild with NuGet restore
    Write-Host "`nRestoring NuGet packages..." -ForegroundColor Yellow
    $nuget = "${env:ProgramFiles(x86)}\NuGet\nuget.exe"
    if (-not (Test-Path $nuget)) {
        Write-Warning "NuGet.exe not found. Attempting to download..."
        $nugetDir = "${env:ProgramFiles(x86)}\NuGet"
        if (-not (Test-Path $nugetDir)) {
            New-Item -ItemType Directory -Path $nugetDir -Force | Out-Null
        }
        try {
            Invoke-WebRequest -Uri "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe" -OutFile $nuget -ErrorAction Stop
        } catch {
            Write-Warning "Failed to download NuGet.exe. MSBuild restore may handle packages automatically."
            $nuget = $null
        }
    }
    
    if ($nuget -and (Test-Path $nuget)) {
        Push-Location "Kvadrat.NesterBridge"
        & $nuget restore packages.config -PackagesDirectory ..\packages
        Pop-Location
    } else {
        Write-Host "Skipping NuGet restore (MSBuild will restore automatically)" -ForegroundColor Yellow
    }
    
    # Build Library
    Write-Host "`nBuilding Kvadrat.NesterBridge (Release, AnyCPU)..." -ForegroundColor Yellow
    & $msbuild "Kvadrat.NesterBridge\Kvadrat.NesterBridge.csproj" /p:Configuration=Release /p:Platform=AnyCPU /t:Clean,Build /verbosity:minimal
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed for Kvadrat.NesterBridge"
        exit 1
    }
    
    # Build Console Test
    Write-Host "`nBuilding BridgeConsoleTest (Release, AnyCPU)..." -ForegroundColor Yellow
    & $msbuild "BridgeConsoleTest\BridgeConsoleTest.csproj" /p:Configuration=Release /p:Platform=AnyCPU /t:Clean,Build /verbosity:minimal
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed for BridgeConsoleTest"
        exit 1
    }
}

# Print output paths
Write-Host "`n=== Build Complete ===" -ForegroundColor Green

$dllPath = "Kvadrat.NesterBridge\bin\Release\Kvadrat.NesterBridge.dll"
$exePath = "BridgeConsoleTest\bin\Release\BridgeConsoleTest.exe"

if (Test-Path $dllPath) {
    $dllPath = Resolve-Path $dllPath
    Write-Host "`nDLL Path:" -ForegroundColor Cyan
    Write-Host $dllPath -ForegroundColor White
} else {
    Write-Warning "DLL not found at expected path: $dllPath"
}

if (Test-Path $exePath) {
    $exePath = Resolve-Path $exePath
    Write-Host "`nEXE Path:" -ForegroundColor Cyan
    Write-Host $exePath -ForegroundColor White
} else {
    Write-Warning "EXE not found at expected path: $exePath"
}

# Copy Newtonsoft.Json.dll to output for distribution
$newtonsoftSource = "packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll"
if (Test-Path $newtonsoftSource) {
    $newtonsoftDest = "Kvadrat.NesterBridge\bin\Release\Newtonsoft.Json.dll"
    Copy-Item $newtonsoftSource -Destination $newtonsoftDest -Force
    Write-Host "`nNewtonsoft.Json.dll copied to output directory" -ForegroundColor Green
}

Write-Host "`nReady for CPQ integration!" -ForegroundColor Green
Write-Host "`nUpload BOTH DLLs to Experlogix:" -ForegroundColor Cyan
Write-Host "  1. Kvadrat.NesterBridge.dll" -ForegroundColor White
Write-Host "  2. Newtonsoft.Json.dll" -ForegroundColor White

