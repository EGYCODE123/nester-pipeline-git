# Quick ILMerge Installation Guide

## Problem
The ILMerge GitHub repository is archived and has no releases. However, ILMerge is available via NuGet.

## Solution Options

### ✅ Option 1: Visual Studio Package Manager Console (Easiest)

If you have Visual Studio:

1. Open the solution in Visual Studio
2. Go to **Tools → NuGet Package Manager → Package Manager Console**
3. Run:
   ```powershell
   Install-Package ilmerge -Version 3.0.41
   ```
4. After installation, copy ILMerge.exe:
   ```powershell
   cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
   Copy-Item "packages\ilmerge.3.0.41\tools\ILMerge.exe" -Destination "tools\ILMerge.exe" -Force
   ```

### ✅ Option 2: Manual Download from NuGet.org

1. Go to: https://www.nuget.org/packages/ilmerge/3.0.41
2. Click **Download package** (right side)
3. Rename the downloaded `.nupkg` file to `.zip`
4. Extract the zip file
5. Navigate to `tools\` folder inside
6. Copy `ILMerge.exe` to `bridges\dotnet\tools\ILMerge.exe`

### ✅ Option 3: Use ILRepack (Recommended Alternative)

ILRepack is actively maintained and works the same way:

1. **Via Visual Studio Package Manager Console:**
   ```powershell
   Install-Package ILRepack
   ```
   Then copy:
   ```powershell
   Copy-Item "packages\ILRepack.*\tools\ILRepack.exe" -Destination "tools\ILMerge.exe" -Force
   ```

2. **Or download directly:**
   - Go to: https://www.nuget.org/packages/ILRepack/
   - Download the package
   - Extract and copy `ILRepack.exe` to `tools\ILMerge.exe`

### ✅ Option 4: Use dotnet CLI (if .NET SDK installed)

```powershell
cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
dotnet tool install --global ilmerge
# Then copy from user profile tools directory
```

## Verify Installation

After installing, verify:

```powershell
Test-Path "Z:\CPQ Waste\nester-pipeline\bridges\dotnet\tools\ILMerge.exe"
```

Should return `True`.

## Build with ILMerge

Once installed, run:

```powershell
cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
powershell -ExecutionPolicy Bypass -File build_with_ilmerge.ps1
```

## Current Workaround

**You can build and test without ILMerge** - the DLL will work, but you'll need to upload both DLLs to Experlogix:
- `Kvadrat.NesterBridge.dll`
- `Newtonsoft.Json.dll`

For a self-contained single DLL, ILMerge (or ILRepack) is required.

## Recommendation

**Use ILRepack** - it's actively maintained and easier to install:
- NuGet Package: https://www.nuget.org/packages/ILRepack/
- Works identically to ILMerge
- Better long-term support



