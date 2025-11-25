Kvadrat Waste API - Experlogix CPQ Integration Guide
=====================================================

This package contains the .NET Bridge DLL for integrating the Kvadrat Waste API with Experlogix CPQ.

FILES INCLUDED:
---------------
- Kvadrat.NesterBridge.dll (Main assembly)
- Newtonsoft.Json.dll (Required dependency - upload BOTH to Experlogix)

INSTALLATION:
-------------
1. Upload BOTH DLLs in Experlogix CPQ Admin:
   - Navigate to: Integration → Manage .NET Assemblies
   - Click "Add Assembly"
   - Browse to and select: Kvadrat.NesterBridge.dll
   - Click "Save"
   - Repeat for: Newtonsoft.Json.dll
   - Verify both assemblies appear with namespaces:
     * Kvadrat.NesterBridge
     * Newtonsoft.Json

CONFIGURATION:
-------------
1. Create the API Query:
   - Navigate to: Data Management → Queries → Category Extension Queries
   - Create a new query named: API_BRIDGE
   - Set Query Type: .NET Assembly
   - Set Source Assembly: Kvadrat.NesterBridge, Version=1.0.4.0, Culture=neutral, PublicKeyToken=null
   - Set Type Name: Kvadrat.NesterBridge.EffClient
   - Set Method: GetEfficiency(String, String, String, Int32)
   - Set Returns: Kvadrat.NesterBridge.EfficiencyResult
   - Set Data Type: Recordset
   
2. Configure Parameters:
   - apiUrl (String) = Source: [API.API_URL] (e.g., "http://localhost:8000/api/v1/waste/efficiency")
   - orderJson (String) = Source: [API.API_Payload] (your JSON payload property)
   - bearerToken (String) = Source: [API.Bearer_Token] (your API token)
   - timeoutSeconds (Int32) = Source: [API.API_Timeout_Seconds] (default: 30)

3. Map Output Fields:
   - After selecting the method and clicking **Reload**, Experlogix will display these fields:
     * SelectedRollWidth_mm (double): Roll width selected in millimeters
     * WastePercent (double): Waste percentage (0-100)
     * UsedLength_m (double): Total fabric length used in meters
     * MarkerCount (int): Number of marker segments
     * EfficiencyPercent (double): Efficiency percentage (0-100)
     * StatusMessage (string): Status message ("ok" on success, error message on failure)
     * CalcId (string): Calculation ID from API response
     * QuoteId (string): Quote identifier
     * LineId (string): Line identifier from first result

4. Create Inbound Property Query (if needed):
   - Navigate to: Data Management → Inbound Property Queries
   - Create: API_BRIDGE_IN
   - Connect to Query: API_BRIDGE
   - Map Output Fields to Properties:
     * SelectedRollWidth_mm → [SelectedRollWidth_mm] (decimal)
     * WastePercent → [WastePercent] (decimal)
     * UsedLength_m → [UsedLength_m] (decimal)
     * MarkerCount → [MarkerCount] (integer)
     * EfficiencyPercent → [EfficiencyPercent] (decimal)
     * StatusMessage → [StatusMessage] (string)
     * CalcId → [CalcId] (string)
     * QuoteId → [QuoteId] (string)
     * LineId → [LineId] (string)

5. Create Rule to Execute:
   - In your CPQ Rules, add:
     * Option: "Calculate Efficiency"
     * Action: Execute Query "API_BRIDGE" or Inbound Property Query "API_BRIDGE_IN"

6. Error Handling:
   - Add rule logic:
     IF [StatusMessage] <> "ok" AND [StatusMessage] <> ""
       SET [CalculationStatus] = "Error"
       SET [ErrorMessage] = [StatusMessage]
     ELSE
       SET [CalculationStatus] = "Success"
       // Use EfficiencyPercent, WastePercent, UsedLength_m, etc. in your calculations
     ENDIF

METHOD SIGNATURE:
----------------
Kvadrat.NesterBridge.EffClient.GetEfficiency(
  String apiUrl,
  String orderJson,
  String bearerToken,
  Int32 timeoutSeconds
)

Returns: Kvadrat.NesterBridge.EfficiencyResult

OUTPUT FIELDS:
--------------
- SelectedRollWidth_mm (double): Roll width selected in millimeters (from first result)
- WastePercent (double): Waste percentage (0-100) from line-level waste_factor_pct
- UsedLength_m (double): Total fabric length used in meters (converted from mm)
- MarkerCount (int): Number of marker segments (from levels)
- EfficiencyPercent (double): Efficiency percentage (0-100) from utilization
- StatusMessage (string): Status message from API response ("ok" on success, error message on failure)
- CalcId (string): Calculation ID from API response
- QuoteId (string): Quote identifier from request
- LineId (string): Line identifier from first result

JSON PAYLOAD FORMAT:
--------------------
The orderJson parameter must be a valid JSON string with this structure:

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

IMPORTANT NOTES:
---------------
- The available_widths_mm field must be a JSON array, not a quoted string
- All width/drop values are in millimeters
- The API requires Bearer token authentication
- Timeout is in seconds (recommended: 30-60 for production)
- Check the StatusMessage field after each call to detect failures
- UsedLength_m is in meters (converted from millimeters in the API response)
- SelectedRollWidth_mm is taken from the first result's roll_width_mm field
- **IMPORTANT**: Upload BOTH DLLs (Kvadrat.NesterBridge.dll AND Newtonsoft.Json.dll) to Experlogix

SECURITY FEATURES:
------------------
- Rate Limiting: Maximum 120 requests per minute
- Concurrency Limiting: Maximum 5 concurrent requests
- Input Validation: URL validation, payload size limits (64 KB max)
- Timeout Control: Configurable per-request timeouts (clamped to 1-300 seconds)
- Error Sanitization: No stack traces or sensitive information leaked

VERSION HISTORY:
---------------
- 1.0.4.0: Strongly-typed EfficiencyResult method with rate limiting and security features
- 1.0.3.0: Updated DataTable structure with Experlogix-compatible column names
- 1.0.2.0: Initial release

SUPPORT:
--------
For API documentation, see: docs/API_CONTRACT.md
For DLL usage examples, see: bridges/dotnet/README.md



