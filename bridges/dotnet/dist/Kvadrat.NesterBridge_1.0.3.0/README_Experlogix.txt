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

2. Upload Newtonsoft.Json.dll (Required dependency):
   - Repeat the above steps for Newtonsoft.Json.dll
   - Or copy it to the same location as Kvadrat.NesterBridge.dll

CONFIGURATION:
-------------
1. Create the API Query:
   - Navigate to: Data Management → Queries → Category Extension Queries
   - Create a new query named: API_BRIDGE
   - Set Query Type: .NET Assembly
   - Set Source Assembly: Kvadrat.NesterBridge, Version=1.0.3.0, Culture=neutral, PublicKeyToken=null
   - Set Type Name: Kvadrat.NesterBridge.EffClient
   - Set Method: GetEfficiency(String, String, String, Int32)
   - Set Returns: System.Data.DataTable
   - Set Data Type: Recordset
   
2. Configure Parameters:
   - apiUrl (String) = Source: [API.API_URL] (e.g., "http://localhost:8000/api/v1/waste/efficiency")
   - orderJson (String) = Source: [API.API_Payload] (your JSON payload property)
   - bearerToken (String) = Source: [API.Bearer_Token] (your API token)
   - timeoutSec (Int32) = Source: [API.API_Timeout_Seconds] (default: 30)

3. Map Output Columns:
   - The DataTable "NesterEfficiency" contains the following columns:
     * SelectedRollWidth_mm (double): Roll width selected in millimeters
     * WastePercent (double): Waste percentage (0-100)
     * UsedLength_m (double): Total fabric length used in meters
     * MarkerCount (int): Number of marker segments
     * EfficiencyPercent (double): Efficiency percentage (0-100)
     * StatusMessage (string): Status message ("ok" on success, error message on failure)

4. Create Inbound Property Query (if needed):
   - Navigate to: Data Management → Inbound Property Queries
   - Create: API_BRIDGE_IN
   - Connect to Query: API_BRIDGE
   - Map Output Columns to Properties:
     * SelectedRollWidth_mm → [SelectedRollWidth_mm] (decimal)
     * WastePercent → [WastePercent] (decimal)
     * UsedLength_m → [UsedLength_m] (decimal)
     * MarkerCount → [MarkerCount] (integer)
     * EfficiencyPercent → [EfficiencyPercent] (decimal)
     * StatusMessage → [StatusMessage] (string)

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
  Int32 timeoutSec
)

Returns: System.Data.DataTable (Recordset)
DataTable Name: "NesterEfficiency"

OUTPUT COLUMNS:
--------------
- SelectedRollWidth_mm (double): Roll width selected in millimeters (from first result)
- WastePercent (double): Overall waste percentage (0-100) from totals.waste_pct
- UsedLength_m (double): Total fabric length used in meters (sum of all results, converted from mm)
- MarkerCount (int): Number of marker segments (from totals.total_levels)
- EfficiencyPercent (double): Overall efficiency percentage (0-100) from totals.eff_pct
- StatusMessage (string): Status message from API response ("ok" on success, error message on failure)

JSON PAYLOAD FORMAT:
--------------------
The orderJson parameter must be a valid JSON string with this structure:

{
  "quote_id": "Q-2025-00123",
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
- Timeout is in seconds (recommended: 30-60 for production)
- Check the StatusMessage column after each call to detect failures
- UsedLength_m is in meters (converted from millimeters in the API response)
- SelectedRollWidth_mm is taken from the first result's roll_width_mm field

VERSION HISTORY:
---------------
- 1.0.3.0: Updated DataTable structure with Experlogix-compatible column names
- 1.0.2.0: Initial release

SUPPORT:
--------
For API documentation, see: docs/API_CONTRACT.md
For DLL usage examples, see: bridges/dotnet/README.md



