Kvadrat Waste API - Experlogix CPQ Integration Guide
=====================================================

This package contains the .NET Bridge DLL for integrating the Kvadrat Waste API with Experlogix CPQ.

FILES INCLUDED:
---------------
- Kvadrat.NesterBridge.dll (Main assembly)
- Newtonsoft.Json.dll (Required dependency)

INSTALLATION:
-------------
1. Upload DLL(s) in Experlogix CPQ Admin:
   - Navigate to: Integration → Manage .NET Assemblies
   - Click "Add Assembly"
   - Browse to and select: Kvadrat.NesterBridge.dll
   - Click "Save"
   - Verify the assembly appears with namespace: Kvadrat.NesterBridge

2. If Newtonsoft.Json.dll is not in the GAC, upload it as well:
   - Repeat the above steps for Newtonsoft.Json.dll
   - Or copy it to the same location as Kvadrat.NesterBridge.dll

CONFIGURATION:
-------------
1. Create the API Query:
   - Navigate to: Data Management → Queries
   - Create a new query named: API_BRIDGE
   - Set Query Type: .NET Assembly
   - Set Method: GetEfficiency
   - Set Data Type: Recordset
   
2. Configure Parameters:
   - apiUrl = Constant: "https://api.kvadrat.local" (or your API URL)
   - orderJson = Property: [ApiPayload] (your JSON payload property)
   - bearerToken = Constant: "YOUR_API_TOKEN" (or use a Property)
   - timeoutSec = 60

3. Create Inbound Property Query:
   - Navigate to: Data Management → Inbound Property Queries
   - Create: API_BRIDGE_IN
   - Connect to Query: API_BRIDGE
   - Map Output Columns to Properties:
     * efficiency_pct → [EfficiencyPct] (decimal)
     * waste_area_m2 → [WasteAreaM2] (decimal)
     * used_length_mm → [UsedLengthMm] (integer)
     * markers_count → [MarkersCount] (integer)
     * tube_bars_required → [TubeBarsRequired] (integer)
     * error → [Error] (string)

4. Create Rule to Execute:
   - In your CPQ Rules, add:
     * Option: "Calculate Efficiency"
     * Action: Execute Inbound Property Query "API_BRIDGE_IN"

5. Error Handling:
   - Add rule logic:
     IF NOT ISNULL([Error]) AND [Error] <> ""
       SET [CalculationStatus] = "Error"
       SET [ErrorMessage] = [Error]
     ELSE
       SET [CalculationStatus] = "Success"
       // Use efficiency_pct, waste_area_m2, etc. in your calculations
     ENDIF

METHOD SIGNATURE:
----------------
Kvadrat.NesterBridge.EffClient.GetEfficiency(
  String apiUrl,
  String orderJson,
  String bearerToken,
  Int32 timeoutSec
)

Returns: System.Data.DataTable (Recordset)

OUTPUT COLUMNS:
--------------
- efficiency_pct (decimal): Overall efficiency percentage (0-100)
- waste_area_m2 (decimal): Total waste area in square meters
- used_length_mm (int): Total fabric length used in millimeters
- markers_count (int): Number of marker segments
- tube_bars_required (int): Number of tube bars (currently 0, reserved for future)
- error (string): Error message if any, null on success

JSON PAYLOAD FORMAT:
--------------------
The orderJson parameter must be a valid JSON string with this structure:

{
  "quote_id": "<QuoteId>",
  "model": "blinds",
  "available_widths_mm": [1900, 2050, 2400, 3000],
  "lines": [
    {
      "line_id": "L1",
      "width_mm": 2400,
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
- Timeout is in seconds (recommended: 60 for production)
- Check the error column after each call to detect failures

SUPPORT:
--------
For API documentation, see: docs/API_CONTRACT.md
For DLL usage examples, see: bridges/dotnet/README.md









