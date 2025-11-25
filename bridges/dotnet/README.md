# Kvadrat.NesterBridge - .NET Bridge DLL for CPQ Integration

## Overview

This .NET Framework 4.8 class library provides a simple bridge for Experlogix CPQ to call the Kvadrat Waste API. It handles HTTP requests, authentication, and JSON parsing, exposing simple static methods that CPQ rules can call.

## Building

### Prerequisites

**IMPORTANT:** You need **Visual Studio** (the IDE) or **Visual Studio Build Tools**, NOT Visual Studio Code.

- **Visual Studio Build Tools 2022** (recommended - free, smaller download)
  - Download: https://visualstudio.microsoft.com/downloads/
  - Select "Build Tools for Visual Studio 2022"
  - During installation, select **".NET desktop build tools"** workload
- **OR Visual Studio 2019/2022** (any edition - Community is free)
  - Download: https://visualstudio.microsoft.com/vs/community/
  - During installation, select **".NET desktop development"** workload
- NuGet command-line tool (auto-downloaded if missing)
- MSBuild (included with Visual Studio/Build Tools)

### Build Steps

1. Open PowerShell in the `bridges/dotnet/` directory
2. Run: `.\build.ps1`

The script will:
- Restore NuGet packages (Newtonsoft.Json 13.0.3)
- Build `Kvadrat.NesterBridge.dll` (Release, AnyCPU)
- Build `BridgeConsoleTest.exe` (Release, AnyCPU)
- Print the output paths

## DLL Structure

### Assembly: `Kvadrat.NesterBridge.dll`
- **Target**: .NET Framework 4.8
- **Platform**: AnyCPU
- **Dependencies**: 
  - Newtonsoft.Json 13.0.3
  - System.Net.Http

### Public Methods

#### `EffClient.GetEfficiency(apiUrl, orderJson, bearerToken, timeoutSec)` ⭐ **NEW - For Experlogix**

Returns a `DataTable` with efficiency metrics for Experlogix CPQ integration.

**Parameters:**
- `apiUrl` (string): Full API endpoint URL (e.g., "http://localhost:8000/api/v1/waste/efficiency")
- `orderJson` (string): JSON string of the order payload
- `bearerToken` (string): Bearer token for authentication
- `timeoutSec` (int): Timeout in seconds (default: 30)

**Returns:** `System.Data.DataTable` with one row containing:
- `efficiency_pct` (decimal): Overall efficiency percentage
- `waste_area_m2` (decimal): Total waste area in square meters
- `used_length_mm` (int): Total fabric length used in millimeters
- `markers_count` (int): Number of marker segments
- `tube_bars_required` (int): Number of tube bars (currently 0, reserved for future)
- `error` (string): Error message if any, null on success

**Example:**
```csharp
DataTable result = EffClient.GetEfficiency(
    "http://localhost:8000/api/v1/waste/efficiency",
    orderJson,
    "YOUR_TOKEN",
    30
);

if (result.Rows.Count > 0)
{
    decimal efficiency = (decimal)result.Rows[0]["efficiency_pct"];
    decimal wasteArea = (decimal)result.Rows[0]["waste_area_m2"];
    int usedLength = (int)result.Rows[0]["used_length_mm"];
    string error = result.Rows[0]["error"] as string;
    
    if (string.IsNullOrEmpty(error))
    {
        // Success - use the values
    }
    else
    {
        // Handle error
    }
}
```

#### `EffClient.GetEfficiencyJson(apiUrl, orderJson, bearerToken, timeoutSec)`

Returns the full JSON response from the API.

**Parameters:**
- `apiUrl` (string): Full API endpoint URL (e.g., "http://localhost:8000/api/v1/waste/efficiency")
- `orderJson` (string): JSON string of the order payload
- `bearerToken` (string): Bearer token for authentication
- `timeoutSec` (int): Timeout in seconds (default: 30)

**Returns:** JSON response string or "ERROR: ..." message

**Example:**
```csharp
string result = EffClient.GetEfficiencyJson(
    "http://localhost:8000/api/v1/waste/efficiency",
    orderJson,
    "YOUR_TOKEN",
    30
);
```

#### `EffClient.GetWasteFactorPct(apiUrl, orderJson, bearerToken, timeoutSec)`

Returns only the `waste_factor_pct` from the first line's result.

**Parameters:** Same as `GetEfficiencyJson`

**Returns:** waste_factor_pct as string (e.g., "15.23") or "ERROR: ..." message

**Example:**
```csharp
string factor = EffClient.GetWasteFactorPct(
    "http://localhost:8000/api/v1/waste/efficiency",
    orderJson,
    "YOUR_TOKEN",
    30
);
```

## Error Handling

Both methods return error messages prefixed with "ERROR:". CPQ should check if the result starts with "ERROR:" to detect failures.

**Error Format:**
- `"ERROR: HTTP 401: ..."` - Authentication failed
- `"ERROR: Timeout after 30 seconds: ..."` - Request timeout
- `"ERROR: HTTP request failed: ..."` - Network error
- `"ERROR: JSON parsing failed: ..."` - Invalid JSON response

## Testing

### Console Tester

Run `BridgeConsoleTest.exe` to test the DLL:

```powershell
.\BridgeConsoleTest\bin\Release\BridgeConsoleTest.exe
```

Or with custom arguments:
```powershell
.\BridgeConsoleTest\bin\Release\BridgeConsoleTest.exe "http://localhost:8000/api/v1/waste/efficiency" "YOUR_TOKEN" "ORDER_JSON" 30
```

The tester will:
1. Call `GetEfficiencyJson` and display the result (truncated)
2. Call `GetWasteFactorPct` and display the waste factor percentage

## TLS Configuration

The DLL enforces TLS 1.2+ for secure connections. The console tester includes `app.config` with strong crypto settings.

## Usage in CPQ

See `docs/EXPERLOGIX_INTEGRATION_DLL.md` for detailed CPQ integration instructions.

## Files

- `Kvadrat.NesterBridge.csproj` - Class library project file
- `EffClient.cs` - Main client class with public methods
- `Properties/AssemblyInfo.cs` - Assembly metadata
- `packages.config` - NuGet package references
- `BridgeConsoleTest/` - Console test application
- `build.ps1` - Build script

