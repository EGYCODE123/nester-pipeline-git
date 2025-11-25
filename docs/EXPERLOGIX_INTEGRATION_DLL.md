# Experlogix CPQ Integration Guide - Kvadrat Waste API

## Overview

This guide explains how to integrate the Kvadrat Waste API with Experlogix CPQ using the `.NET Bridge DLL`. The DLL provides simple static methods that CPQ rules can call to calculate waste efficiency.

## Prerequisites

1. **Kvadrat.NesterBridge.dll** built and available (see `bridges/dotnet/README.md`)
2. Experlogix CPQ with .NET integration enabled
3. API endpoint URL and Bearer token

## Step 1: Import the DLL into CPQ

1. Open Experlogix CPQ Admin
2. Navigate to **Integration → Manage .NET Assemblies**
3. Click **Add Assembly**
4. Browse to: `bridges\dotnet\Kvadrat.NesterBridge\bin\Release\Kvadrat.NesterBridge.dll`
5. Click **Save**
6. Verify the assembly appears in the list with namespace: `Kvadrat.NesterBridge`

**Note:** The DLL includes `Newtonsoft.Json.dll` as a dependency. If Experlogix requires it separately, copy `packages\Newtonsoft.Json.13.0.3\lib\net45\Newtonsoft.Json.dll` to the same location as the main DLL.

## Step 2: Build the Order JSON Payload

CPQ must construct a JSON payload that matches the API contract. The JSON **MUST** include `available_widths_mm` as an array of integers.

### JSON Structure

```json
{
  "quote_id": "<[QuoteId]>",
  "model": "<[Model]>",
  "available_widths_mm": <[AvailableWidthsMM]>,
  "lines": [
    {
      "line_id": "L1",
      "width_mm": <[Width_mm]>,
      "drop_mm": <[Drop_mm]>,
      "qty": <[Qty]>,
      "fabric_code": "<[FabricCode]>",
      "series": "<[Series]>"
    }
  ]
}
```

### Critical: `available_widths_mm` Format

The `available_widths_mm` field **must be a valid JSON array**, not a quoted string.

**Correct:**
```json
"available_widths_mm": [1900, 2050, 2400, 3000]
```

**Incorrect:**
```json
"available_widths_mm": "[1900, 2050, 2400, 3000]"  // ❌ This is a string, not an array
```

### CPQ JSON Builder Example

If CPQ provides a comma-separated list, convert it to a JSON array:

```
// If CPQ variable [AvailableWidthsMM] = "1900,2050,2400,3000"
// Convert to array format:
CONCATENATE("[", REPLACE([AvailableWidthsMM], ",", ", "), "]")
// Result: "[1900, 2050, 2400, 3000]"
```

Or use CPQ's JSON array functions if available.

### Complete JSON Builder Example

```
CONCATENATE(
  "{",
  "\"quote_id\": \"", [QuoteId], "\",",
  "\"model\": \"", [Model], "\",",
  "\"available_widths_mm\": ", [AvailableWidthsMM], ",",
  "\"lines\": [",
  "{",
  "\"line_id\": \"L1\",",
  "\"width_mm\": ", [Width_mm], ",",
  "\"drop_mm\": ", [Drop_mm], ",",
  "\"qty\": ", [Qty], ",",
  "\"fabric_code\": \"", [FabricCode], "\",",
  "\"series\": \"", [Series], "\"",
  "}",
  "]",
  "}"
)
```

Store this in a CPQ variable: `[OrderJson]`

## Step 3: Call the DLL from CPQ Rules

### Method 1: Get DataTable (RECOMMENDED for Experlogix) ⭐

Use `GetEfficiency` to get a DataTable/Recordset that Experlogix can map directly:

**CPQ Rule Call:**
```
Kvadrat.NesterBridge.EffClient.GetEfficiency(
  [ApiUrl],
  [OrderJson],
  [ApiToken],
  [TimeoutSec]
)
```

**Parameters:**
- `[ApiUrl]` - Full API URL (e.g., "http://your-server:8000/api/v1/waste/efficiency")
- `[OrderJson]` - JSON payload built in Step 2
- `[ApiToken]` - Bearer token (e.g., "YOUR_TOKEN")
- `[TimeoutSec]` - Timeout in seconds (e.g., "60")

**Store Result:** Save to `[EfficiencyTable]` (DataTable/Recordset type)

**In Data Management → Queries:**
- Query Type: `.NET Assembly`
- Method: `GetEfficiency`
- **Data Type: Recordset**
- Inputs:
  - `apiUrl` = Constant (e.g., "https://api.kvadrat.local")
  - `orderJson` = Property `[ApiPayload]`
  - `bearerToken` = Constant or Property
  - `timeoutSec` = 60
- Output Mappings: Map the six columns to properties:
  - `efficiency_pct` → `[EfficiencyPct]` (decimal)
  - `waste_area_m2` → `[WasteAreaM2]` (decimal)
  - `used_length_mm` → `[UsedLengthMm]` (int)
  - `markers_count` → `[MarkersCount]` (int)
  - `tube_bars_required` → `[TubeBarsRequired]` (int)
  - `error` → `[Error]` (string)

**Error Handling:**
```
IF NOT ISNULL([Error]) AND [Error] <> ""
  SET [CalculationStatus] = "Error"
  SET [ErrorMessage] = [Error]
ELSE
  SET [CalculationStatus] = "Success"
  // Use efficiency_pct, waste_area_m2, etc.
ENDIF
```

### Method 2: Get Full JSON Response

Use `GetEfficiencyJson` to get the complete response:

**CPQ Rule Call:**
```
Kvadrat.NesterBridge.EffClient.GetEfficiencyJson(
  [ApiUrl],
  [OrderJson],
  [ApiToken],
  [TimeoutSec]
)
```

**Parameters:**
- `[ApiUrl]` - Full API URL (e.g., "http://your-server:8000/api/v1/waste/efficiency")
- `[OrderJson]` - JSON payload built in Step 2
- `[ApiToken]` - Bearer token (e.g., "YQAKNgR68GvWoB0Ij3zwFirpdDhtb9ST4c5ZaVHUkP2M1xJq")
- `[TimeoutSec]` - Timeout in seconds (e.g., "30")

**Store Result:** Save to `[RawResponse]`

**Error Checking:**
```
IF STARTS_WITH([RawResponse], "ERROR:")
  SET [ErrorFlag] = "true"
  SET [ErrorMessage] = [RawResponse]
ELSE
  SET [ErrorFlag] = "false"
ENDIF
```

**Extract Values (if not error):**
- Use CPQ's JSON parsing functions to extract:
  - `calc_id` - Calculation ID for tracking
  - `results[0].waste_factor_pct` - First line's waste factor
  - `results[0].utilization` - First line's utilization
  - `totals.eff_pct` - Overall efficiency percentage
  - `totals.waste_pct` - Overall waste percentage
  - `totals.total_waste_area_m2` - Total waste area

### Method 2: Get Waste Factor Only (Simpler)

If CPQ lacks JSON parsing helpers, use `GetWasteFactorPct`:

**CPQ Rule Call:**
```
Kvadrat.NesterBridge.EffClient.GetWasteFactorPct(
  [ApiUrl],
  [OrderJson],
  [ApiToken],
  [TimeoutSec]
)
```

**Store Result:** Save to `[WasteFactorPct]`

**Error Checking:**
```
IF STARTS_WITH([WasteFactorPct], "ERROR:")
  SET [ErrorFlag] = "true"
  SET [ErrorMessage] = [WasteFactorPct]
ELSE
  SET [ErrorFlag] = "false"
  // [WasteFactorPct] now contains numeric value like "15.23"
ENDIF
```

## Step 4: Handle Errors

Both methods return error messages prefixed with "ERROR:". Always check for this prefix:

**Error Examples:**
- `"ERROR: HTTP 401: unauthorized"` - Invalid token
- `"ERROR: Timeout after 30 seconds: ..."` - Request timeout
- `"ERROR: HTTP request failed: ..."` - Network/server error
- `"ERROR: JSON parsing failed: ..."` - Invalid response format

**CPQ Error Handling Pattern:**
```
IF STARTS_WITH([Result], "ERROR:")
  // Log error
  SET [CalculationStatus] = "Error"
  SET [ErrorMessage] = [Result]
  // Optionally show error to user or use default values
ELSE
  SET [CalculationStatus] = "Success"
  // Process successful result
ENDIF
```

## Step 5: Use Results in CPQ

### Available Output Fields (from full JSON response)

**Per-Line Results (`results` array):**
- `line_id` - Line identifier
- `waste_factor_pct` - Waste percentage (0-100)
- `utilization` - Utilization percentage (0-100)
- `used_length_mm` - Fabric length used in millimeters
- `blind_area_m2` - Blind area in square meters
- `roll_area_m2` - Roll area used in square meters
- `waste_area_m2` - Waste area in square meters
- `roll_width_mm` - Roll width used in millimeters
- `pieces` - Number of pieces
- `levels` - Number of shelf levels

**Totals:**
- `eff_pct` - Overall efficiency percentage (0-100)
- `waste_pct` - Overall waste percentage (0-100)
- `total_area_m2` - Total blind area in square meters
- `total_used_area_m2` - Total roll area used in square meters
- `total_waste_area_m2` - Total waste area in square meters
- `total_pieces` - Total number of pieces
- `total_levels` - Total number of levels

### Example: Store Waste Factor

```
IF [ErrorFlag] = "false"
  // Extract waste_factor_pct from first line
  SET [Line1WasteFactor] = JSON_EXTRACT([RawResponse], "results[0].waste_factor_pct")
  SET [OverallEfficiency] = JSON_EXTRACT([RawResponse], "totals.eff_pct")
  SET [OverallWaste] = JSON_EXTRACT([RawResponse], "totals.waste_pct")
ENDIF
```

## Configuration Variables

Create these CPQ variables:

- `[ApiUrl]` - API endpoint URL (e.g., "http://your-server:8000/api/v1/waste/efficiency")
- `[ApiToken]` - Bearer token (store securely)
- `[TimeoutSec]` - Timeout in seconds (default: "30")
- `[AvailableWidthsMM]` - JSON array of available widths (e.g., "[1900, 2050, 2400, 3000]")
- `[OrderJson]` - Complete JSON payload (built from quote data)
- `[RawResponse]` - Full API response JSON
- `[WasteFactorPct]` - Waste factor percentage (if using GetWasteFactorPct)
- `[ErrorFlag]` - Boolean error indicator
- `[ErrorMessage]` - Error message text

## Testing

### Test with Console Tester

Before integrating into CPQ, test the DLL:

```powershell
cd "Z:\CPQ Waste\nester-pipeline\bridges\dotnet"
.\BridgeConsoleTest\bin\Release\BridgeConsoleTest.exe
```

Or with custom values:
```powershell
.\BridgeConsoleTest\bin\Release\BridgeConsoleTest.exe `
  "http://localhost:8000/api/v1/waste/efficiency" `
  "YOUR_TOKEN" `
  '{"quote_id":"Q-1","model":"blinds","available_widths_mm":[1900,2400],"lines":[{"line_id":"L1","width_mm":2400,"drop_mm":2100,"qty":2}]}'
```

### Test in CPQ

1. Create a test quote with sample line items
2. Build the JSON payload using the formula from Step 2
3. Call the DLL method in a CPQ rule
4. Verify the response is stored correctly
5. Check error handling with invalid token/test data

## Troubleshooting

### DLL Not Found

- Verify DLL is in the correct location
- Check assembly is imported in CPQ (Integration → Manage .NET Assemblies)
- Verify namespace: `Kvadrat.NesterBridge`

### "ERROR: HTTP 401"

- Check Bearer token is correct
- Verify token is not expired
- Ensure Authorization header format is correct

### "ERROR: Timeout"

- Check API server is running
- Verify network connectivity
- Increase timeout value
- Check firewall rules

### Invalid JSON Response

- Verify `available_widths_mm` is a JSON array, not a string
- Check all required fields are present
- Validate JSON syntax (use JSON validator)

### CPQ Cannot Parse JSON

- Use `GetWasteFactorPct` instead of `GetEfficiencyJson` for simpler extraction
- Or use CPQ's built-in JSON parsing functions if available

## Example CPQ Rule Flow

```
1. Build [OrderJson] from quote data
2. Set [ApiUrl] = "http://your-server:8000/api/v1/waste/efficiency"
3. Set [ApiToken] = "YOUR_TOKEN"
4. Set [TimeoutSec] = "30"
5. Call DLL: [RawResponse] = Kvadrat.NesterBridge.EffClient.GetEfficiencyJson([ApiUrl], [OrderJson], [ApiToken], [TimeoutSec])
6. Check error: IF STARTS_WITH([RawResponse], "ERROR:") THEN ...
7. Extract values: [WasteFactor] = JSON_EXTRACT([RawResponse], "results[0].waste_factor_pct")
8. Use [WasteFactor] in downstream calculations
```

## Notes

- The DLL uses TLS 1.2+ for secure connections
- All timeouts are in seconds
- Error messages always start with "ERROR:"
- The `available_widths_mm` field is **required** in the JSON payload
- No pricing calculations are included - only waste efficiency metrics

## Support

For issues:
1. Check CPQ logs for error messages
2. Test with console tester first
3. Verify API is accessible via curl/Postman
4. Review API_CONTRACT.md for request/response format

