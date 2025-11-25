# ILMerge Configuration

## Overview

The `Kvadrat.NesterBridge` project uses **ILMerge** to merge `Newtonsoft.Json.dll` into the main DLL, creating a self-contained assembly that meets Experlogix CPQ requirements.

## Configuration

ILMerge is configured in `Kvadrat.NesterBridge.csproj` via an `AfterBuild` target that:

1. Checks for ILMerge.exe at `tools\ILMerge.exe`
2. Merges `Newtonsoft.Json.dll` into `Kvadrat.NesterBridge.dll`
3. Outputs the merged DLL as `Kvadrat.NesterBridge.Merged.dll` in `bin\Release\ILMerge\`

## Building with ILMerge

### Option 1: Automatic (if ILMerge is present)

If `tools\ILMerge.exe` exists, the build script will automatically run ILMerge after building:

```powershell
cd bridges\dotnet
.\build.ps1
```

The merged DLL will be created at:
```
Kvadrat.NesterBridge\bin\Release\ILMerge\Kvadrat.NesterBridge.Merged.dll
```

### Option 2: Using build_with_ilmerge.ps1

The dedicated build script handles ILMerge setup and execution:

```powershell
cd bridges\dotnet
.\build_with_ilmerge.ps1
```

This script will:
- Download ILMerge if not present
- Build the project
- Merge Newtonsoft.Json into the main DLL
- Optionally sign the merged DLL if a `.snk` file exists

## Manual ILMerge Setup

If you need to set up ILMerge manually:

1. Download ILMerge from: https://github.com/dotnet/ILMerge/releases
2. Place `ILMerge.exe` in `bridges\dotnet\tools\ILMerge.exe`
3. Run the build script

## Output Files

After a successful build with ILMerge:

- **Original DLL**: `Kvadrat.NesterBridge\bin\Release\Kvadrat.NesterBridge.dll` (for local testing)
- **Merged DLL**: `Kvadrat.NesterBridge\bin\Release\ILMerge\Kvadrat.NesterBridge.Merged.dll` (for Experlogix upload)

## Uploading to Experlogix

**IMPORTANT**: Only upload the **merged DLL** (`Kvadrat.NesterBridge.Merged.dll`) to Experlogix CPQ.

The merged DLL is self-contained and includes all dependencies, meeting Experlogix's requirement that assemblies have no external dependencies unless in the GAC.

## Strong Name Signing (Optional)

To strong-name sign the merged DLL:

1. Create a key file:
   ```powershell
   sn -k Kvadrat.NesterBridge\Kvadrat.NesterBridge.snk
   ```

2. The build will automatically sign the assembly if the `.snk` file exists

3. After ILMerge, re-sign the merged DLL:
   ```powershell
   sn -R Kvadrat.NesterBridge\bin\Release\ILMerge\Kvadrat.NesterBridge.Merged.dll Kvadrat.NesterBridge\Kvadrat.NesterBridge.snk
   ```

## Troubleshooting

### ILMerge not found

If you see "ILMerge not found", either:
- Run `build_with_ilmerge.ps1` which will download it automatically
- Manually download and place `ILMerge.exe` in `tools\ILMerge.exe`

### Merge fails

- Ensure `Newtonsoft.Json.dll` exists at `packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll`
- Check that the build completed successfully before ILMerge runs
- Verify ILMerge.exe is the correct version (3.0.41 or later)

### Merged DLL doesn't work

- Verify the merged DLL size is larger than the original (should include Newtonsoft.Json)
- Test the merged DLL locally before uploading to Experlogix
- Check that all required .NET Framework 4.8 dependencies are available



