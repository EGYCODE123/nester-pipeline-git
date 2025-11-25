# Experlogix CPQ Integration Notes

## Assembly Configuration

When configuring the query in Experlogix Design Center, use the following settings:

### Source Assembly
```
Kvadrat.NesterBridge.Merged.dll
```

**Important**: Use the **merged DLL** (`Kvadrat.NesterBridge.Merged.dll`), not the original DLL. The merged DLL is self-contained and includes all dependencies.

### Class
```
Kvadrat.NesterBridge.EffClient
```

### Method
```
GetEfficiency(String apiUrl, String orderJson, String bearerToken, Int32 timeoutSeconds)
```

### Return Type
```
Kvadrat.NesterBridge.EfficiencyResult
```

## Available Fields

After selecting the `GetEfficiency` method and clicking **Reload**, Experlogix will display the following fields from `EfficiencyResult`:

### Primary Metrics
- **SelectedRollWidth_mm** (double): Roll width selected in millimeters
- **WastePercent** (double): Waste percentage (0-100)
- **UsedLength_m** (double): Total fabric length used in meters
- **MarkerCount** (int): Number of marker segments
- **EfficiencyPercent** (double): Efficiency percentage (0-100)

### Status and Metadata
- **StatusMessage** (string): Status message ("ok" on success, error message on failure)
- **CalcId** (string): Calculation ID from API response
- **QuoteId** (string): Quote identifier
- **LineId** (string): Line identifier from first result

## Field Mapping

Map these fields directly to CPQ properties:

```
SelectedRollWidth_mm → [SelectedRollWidth_mm] (decimal)
WastePercent → [WastePercent] (decimal)
UsedLength_m → [UsedLength_m] (decimal)
MarkerCount → [MarkerCount] (integer)
EfficiencyPercent → [EfficiencyPercent] (decimal)
StatusMessage → [StatusMessage] (string)
CalcId → [CalcId] (string)
QuoteId → [QuoteId] (string)
LineId → [LineId] (string)
```

## Error Handling

The `StatusMessage` field indicates success or failure:

- **Success**: `StatusMessage == "ok"`
- **Error**: `StatusMessage` contains a human-readable error message

### Example Error Handling Rule

```vb
IF [StatusMessage] <> "ok" AND [StatusMessage] <> ""
    SET [CalculationStatus] = "Error"
    SET [ErrorMessage] = [StatusMessage]
ELSE
    SET [CalculationStatus] = "Success"
    // Use efficiency metrics in calculations
ENDIF
```

## Method Parameters

### apiUrl (String)
Full HTTP(S) URL to the Nester API endpoint:
```
http://localhost:8000/api/v1/waste/efficiency
```
or
```
https://api.example.com/api/v1/waste/efficiency
```

**Source**: Constant or Property (e.g., `[API.API_URL]`)

### orderJson (String)
JSON payload with order line data. Must match this exact structure:

```json
{
  "quote_id": "Q-TEST-001",
  "model": "blinds",
  "available_widths_mm": [1900, 2050, 2400, 3000],
  "lines": [
    {
      "line_id": "L1",
      "width_mm": 2300,
      "drop_mm": 2100,
      "qty": 2,
      "fabric_code": "FAB001",
      "series": "SERIES-A"
    }
  ]
}
```

**Source**: Property containing the JSON string (e.g., `[API.API_Payload]`)

**Important**: The `available_widths_mm` field must be a JSON array, not a quoted string.

### bearerToken (String)
Optional bearer token for API authentication. Leave empty if not required.

**Source**: Constant or Property (e.g., `[API.Bearer_Token]`)

### timeoutSeconds (Int32)
Request timeout in seconds. Valid range: 1-300. Recommended: 30-60 seconds.

**Source**: Constant or Property (e.g., `[API.API_Timeout_Seconds]`)

## Security Features

The implementation includes:

- **Rate Limiting**: Maximum 120 requests per minute
- **Concurrency Limiting**: Maximum 5 concurrent requests
- **Input Validation**: URL validation, payload size limits (64 KB max)
- **Timeout Control**: Configurable per-request timeouts
- **Error Sanitization**: No stack traces or sensitive information leaked

## Rate Limiting

If rate limits are exceeded, `StatusMessage` will contain:
```
"Rate limit exceeded. Please try again shortly."
```

The method will return safe default values (WastePercent=100, EfficiencyPercent=0).

## Best Practices

1. **Always check StatusMessage**: Verify `StatusMessage == "ok"` before using efficiency metrics
2. **Handle errors gracefully**: Use the StatusMessage field to display user-friendly error messages
3. **Set appropriate timeouts**: Use 30-60 seconds for production, shorter for testing
4. **Validate JSON payload**: Ensure the orderJson matches the expected structure before calling
5. **Use merged DLL**: Always upload `Kvadrat.NesterBridge.Merged.dll`, not the original DLL

## Migration from DataTable Method

If you were previously using the `GetEfficiencyDataTable` method:

1. Update the query to use `GetEfficiency` instead
2. Change return type from `System.Data.DataTable` to `Kvadrat.NesterBridge.EfficiencyResult`
3. Map fields directly instead of using DataTable column names
4. Update error handling to check `StatusMessage` instead of an error column

## Support

For API documentation, see: `docs/API_CONTRACT.md`
For ILMerge setup, see: `README_ILMerge.md`



