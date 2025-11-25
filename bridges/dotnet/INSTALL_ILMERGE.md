# Installing ILMerge

## Important Note

The ILMerge GitHub repository was archived in March 2021 and no longer hosts releases. However, **ILMerge is still available via NuGet** and works perfectly for our needs.

## Quick Setup via NuGet (Recommended)

### Option 1: NuGet Package Manager Console (Visual Studio)

If you have Visual Studio open:

1. Open **Package Manager Console** (Tools → NuGet Package Manager → Package Manager Console)
2. Run:
   ```powershell
   Install-Package ilmerge -Version 3.0.41
   ```
3. Copy ILMerge.exe to the tools folder:
   ```powershell
   cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
   Copy-Item "packages\ilmerge.3.0.41\tools\ILMerge.exe" -Destination "tools\ILMerge.exe" -Force
   ```

### Option 2: NuGet CLI

If you have NuGet CLI installed:

```powershell
cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
nuget install ilmerge -OutputDirectory tools -Version 3.0.41 -ExcludeVersion
Copy-Item "tools\ilmerge\tools\net452\ILMerge.exe" -Destination "tools\ILMerge.exe" -Force
```

### Option 3: Automatic via Build Script

The `build_with_ilmerge.ps1` script will automatically try to install ILMerge via NuGet if NuGet.exe is available:

```powershell
cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
powershell -ExecutionPolicy Bypass -File build_with_ilmerge.ps1
```

## Alternative: ILRepack

If you prefer an actively maintained alternative, you can use **ILRepack**:

```powershell
nuget install ILRepack -OutputDirectory tools
Copy-Item "tools\ILRepack\tools\ILRepack.exe" -Destination "tools\ILMerge.exe" -Force
```

ILRepack is compatible with ILMerge command-line arguments and works the same way.

## Verify Installation

After installation, verify ILMerge exists:

```powershell
Test-Path "Z:\CPQ Waste\nester-pipeline\bridges\dotnet\tools\ILMerge.exe"
```

Should return `True`.

## Building with ILMerge

Once ILMerge is installed, run:

```powershell
cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
powershell -ExecutionPolicy Bypass -File build_with_ilmerge.ps1
```

The merged DLL will be created at:
```
Kvadrat.NesterBridge\bin\Release\ILMerge\Kvadrat.NesterBridge.Merged.dll
```

## NuGet Package Information

- **Package Name**: `ilmerge`
- **Version**: `3.0.41` (latest)
- **NuGet URL**: https://www.nuget.org/packages/ilmerge/
- **Published**: July 9, 2020

## Troubleshooting

### NuGet not found

If NuGet.exe is not available:
1. Download NuGet.exe from: https://www.nuget.org/downloads
2. Place it in: `C:\Program Files (x86)\NuGet\nuget.exe` or in the project directory

### ILMerge path not found

Ensure the tools directory exists:
```powershell
New-Item -ItemType Directory -Path "tools" -Force
```

### Build script fails

If the build script fails to find ILMerge:
1. Manually install via NuGet (Option 1 or 2 above)
2. Verify `tools\ILMerge.exe` exists
3. Run the build script again

## References

- ILMerge NuGet Package: https://www.nuget.org/packages/ilmerge/
- ILRepack (Alternative): https://www.nuget.org/packages/ILRepack/
