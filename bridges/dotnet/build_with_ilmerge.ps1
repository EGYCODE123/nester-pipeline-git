# Build script for Kvadrat.NesterBridge DLL with ILMerge and Strong Name Signing
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot"

Write-Host "=== Building Kvadrat.NesterBridge with ILMerge ===" -ForegroundColor Cyan

# Try to find MSBuild
$msbuild = $null
$msbuildPaths = @(
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
)

foreach ($path in $msbuildPaths) {
    if (Test-Path $path) {
        $msbuild = $path
        break
    }
}

if (-not $msbuild) {
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -requires Microsoft.Component.MSBuild -find MSBuild\**\Bin\MSBuild.exe | Select-Object -First 1
        if ($vsPath -and (Test-Path $vsPath)) {
            $msbuild = $vsPath
        }
    }
}

if (-not $msbuild) {
    Write-Error "MSBuild not found. Please install Visual Studio Build Tools."
    exit 1
}

Write-Host "Using MSBuild: $msbuild" -ForegroundColor Gray

# Check for strong name key file
$snkPath = "Kvadrat.NesterBridge\Kvadrat.NesterBridge.snk"
$hasSnk = Test-Path $snkPath
if ($hasSnk) {
    Write-Host "Strong name key file found - assembly will be signed" -ForegroundColor Green
} else {
    Write-Host "Strong name key file not found - assembly will be unsigned" -ForegroundColor Yellow
    Write-Host "  To create a key file, run: sn -k `"$snkPath`"" -ForegroundColor Gray
}

# Restore NuGet packages (MSBuild will handle this automatically if needed)
Write-Host "`nChecking NuGet packages..." -ForegroundColor Yellow
$nuget = $null
$nugetPaths = @(
    "${env:ProgramFiles(x86)}\NuGet\nuget.exe",
    "nuget.exe",
    "$PSScriptRoot\nuget.exe"
)

foreach ($path in $nugetPaths) {
    if (Test-Path $path) {
        $nuget = $path
        break
    }
}

if ($nuget -and (Test-Path $nuget)) {
    Write-Host "Restoring NuGet packages..." -ForegroundColor Yellow
    $nugetFullPath = Resolve-Path $nuget -ErrorAction SilentlyContinue
    if ($nugetFullPath) {
        Push-Location "Kvadrat.NesterBridge"
        try {
            & "$nugetFullPath" restore packages.config -PackagesDirectory ..\packages 2>&1 | Out-Null
        } catch {
            Write-Host "NuGet restore failed, continuing..." -ForegroundColor Yellow
        }
        Pop-Location
    }
} else {
    Write-Host "NuGet.exe not found - MSBuild will restore packages automatically" -ForegroundColor Gray
}

# Install ILMerge via NuGet if not present
$ilmergePath = "tools\ILMerge.exe"
if (-not (Test-Path $ilmergePath)) {
    Write-Host "`nILMerge not found. Installing via NuGet..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "tools" -Force | Out-Null
    
    # Try to install ILMerge via NuGet
    $nugetInstalled = $false
    if ($nuget -and (Test-Path $nuget)) {
        $nugetFullPath = Resolve-Path $nuget -ErrorAction SilentlyContinue
        if ($nugetFullPath) {
            Write-Host "Installing ILMerge NuGet package..." -ForegroundColor Yellow
            try {
                Push-Location $PSScriptRoot
                & "$nugetFullPath" install ilmerge -OutputDirectory tools -Version 3.0.41 -ExcludeVersion 2>&1 | Out-Null
                
                # ILMerge NuGet package structure: tools\ilmerge\tools\net452\ILMerge.exe
                if (Test-Path "tools\ilmerge\tools\net452\ILMerge.exe") {
                    Copy-Item "tools\ilmerge\tools\net452\ILMerge.exe" -Destination $ilmergePath -Force
                    $nugetInstalled = $true
                    Write-Host "ILMerge installed successfully via NuGet" -ForegroundColor Green
                } elseif (Test-Path "tools\ilmerge\tools\ILMerge.exe") {
                    Copy-Item "tools\ilmerge\tools\ILMerge.exe" -Destination $ilmergePath -Force
                    $nugetInstalled = $true
                    Write-Host "ILMerge installed successfully via NuGet" -ForegroundColor Green
                }
                Pop-Location
            } catch {
                Write-Warning "NuGet installation failed: $_"
                Pop-Location
            }
        }
    }
    
    if (-not $nugetInstalled) {
        Write-Warning "Failed to install ILMerge automatically"
        Write-Host ""
        Write-Host "Please install ILMerge manually using one of these methods:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Option 1: Via NuGet Package Manager Console:" -ForegroundColor Cyan
        Write-Host "  Install-Package ilmerge -Version 3.0.41" -ForegroundColor White
        Write-Host "  Then copy ILMerge.exe from packages\ilmerge.3.0.41\tools\ to tools\ILMerge.exe" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Option 2: Via NuGet CLI:" -ForegroundColor Cyan
        Write-Host "  nuget install ilmerge -OutputDirectory tools -Version 3.0.41" -ForegroundColor White
        Write-Host ""
        Write-Host "Option 3: Use ILRepack (alternative, actively maintained):" -ForegroundColor Cyan
        Write-Host "  nuget install ILRepack -OutputDirectory tools" -ForegroundColor White
        Write-Host ""
        Write-Host "Note: ILMerge repository is archived. Use NuGet package instead." -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
} else {
    Write-Host "ILMerge found at: $ilmergePath" -ForegroundColor Green
}

# Build Library
Write-Host "`nBuilding Kvadrat.NesterBridge (Release, AnyCPU)..." -ForegroundColor Yellow
& $msbuild "Kvadrat.NesterBridge\Kvadrat.NesterBridge.csproj" /p:Configuration=Release /p:Platform=AnyCPU /t:Clean,Build /verbosity:minimal

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed for Kvadrat.NesterBridge"
    exit 1
}

# Paths
$originalDll = "Kvadrat.NesterBridge\bin\Release\Kvadrat.NesterBridge.dll"
$newtonsoftDll = "packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll"
$mergedDll = "Kvadrat.NesterBridge\bin\Release\Kvadrat.NesterBridge.Merged.dll"
$finalDll = "Kvadrat.NesterBridge\bin\Release\Kvadrat.NesterBridge.dll"

# Verify files exist
if (-not (Test-Path $originalDll)) {
    Write-Error "Original DLL not found: $originalDll"
    exit 1
}

if (-not (Test-Path $newtonsoftDll)) {
    Write-Error "Newtonsoft.Json.dll not found: $newtonsoftDll"
    exit 1
}

# Merge assemblies using ILMerge
Write-Host "`nMerging assemblies with ILMerge..." -ForegroundColor Yellow
$ilmergeArgs = @(
    "/lib:packages\Newtonsoft.Json.13.0.3\lib\net45",
    "/out:`"$mergedDll`"",
    "/target:library",
    "/targetplatform:v4,`"$([System.Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory())`"",
    "/internalize",
    "`"$originalDll`"",
    "`"$newtonsoftDll`""
)

& $ilmergePath $ilmergeArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "ILMerge failed"
    exit 1
}

# Replace original DLL with merged DLL
Write-Host "Replacing original DLL with merged DLL..." -ForegroundColor Yellow
Copy-Item $mergedDll -Destination $finalDll -Force
Remove-Item $mergedDll -Force

# Sign the merged DLL if key file exists
if ($hasSnk) {
    Write-Host "Signing merged DLL..." -ForegroundColor Yellow
    $snExe = "${env:ProgramFiles(x86)}\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\sn.exe"
    if (-not (Test-Path $snExe)) {
        $snExe = "${env:ProgramFiles}\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\sn.exe"
    }
    
    if (Test-Path $snExe) {
        & $snExe -R "`"$finalDll`" `"$snkPath`"" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "DLL signed successfully" -ForegroundColor Green
        } else {
            Write-Warning "Signing failed - DLL may be unsigned"
        }
    } else {
        Write-Warning "sn.exe not found - DLL is unsigned"
    }
}

# Print output paths
Write-Host "`n=== Build Complete ===" -ForegroundColor Green

$dllPath = Resolve-Path $finalDll
Write-Host "`nMerged DLL Path:" -ForegroundColor Cyan
Write-Host $dllPath -ForegroundColor White

# Verify the merged DLL
$dllInfo = Get-Item $dllPath
Write-Host "`nDLL Size: $([math]::Round($dllInfo.Length / 1KB, 2)) KB" -ForegroundColor Gray

# Check if Newtonsoft.Json is merged (merged DLL should be larger)
$originalSize = (Get-Item $originalDll).Length
$mergedSize = $dllInfo.Length
if ($mergedSize -gt $originalSize) {
    Write-Host "[OK] Newtonsoft.Json successfully merged into DLL" -ForegroundColor Green
} else {
    Write-Warning "DLL size suggests merge may have failed"
}

Write-Host "`nReady for CPQ integration!" -ForegroundColor Green
Write-Host "`nNote: This DLL is self-contained and includes Newtonsoft.Json" -ForegroundColor Cyan

