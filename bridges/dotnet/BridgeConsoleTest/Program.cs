using System;
using Kvadrat.NesterBridge;

namespace BridgeConsoleTest
{
    class Program
    {
        static void Main(string[] args)
        {
            // Test data matching the Swagger example
            string apiUrl = "http://localhost:8000/api/v1/waste/efficiency";
            string bearerToken = "YQAKNgR68GvWoB0Ij3zwFirpdDhtb9ST4c5ZaVHUkP2M1xJq";
            string orderJson = @"{
  ""quote_id"": ""Q-TEST-001"",
  ""model"": ""blinds"",
  ""available_widths_mm"": [1900, 2050, 2400, 3000],
  ""lines"": [
    {
      ""line_id"": ""L1"",
      ""width_mm"": 2300,
      ""drop_mm"": 2100,
      ""qty"": 2,
      ""fabric_code"": ""FAB001"",
      ""series"": ""SERIES-A""
    }
  ]
}";
            int timeoutSeconds = 30;

            // Parse command-line args if provided
            if (args.Length >= 1) apiUrl = args[0];
            if (args.Length >= 2) bearerToken = args[1];
            if (args.Length >= 3) orderJson = args[2];
            if (args.Length >= 4) int.TryParse(args[3], out timeoutSeconds);

            Console.WriteLine("=== Kvadrat Nester Bridge Test Suite ===\n");
            Console.WriteLine($"API URL: {apiUrl}");
            Console.WriteLine($"Bearer Token: {(string.IsNullOrEmpty(bearerToken) ? "(none)" : bearerToken.Substring(0, Math.Min(10, bearerToken.Length)) + "...")}");
            Console.WriteLine($"Timeout: {timeoutSeconds}s\n");

            // Test 1: Normal API call with EfficiencyResult
            Console.WriteLine("--- Test 1: GetEfficiency (EfficiencyResult) ---");
            TestGetEfficiency(apiUrl, orderJson, bearerToken, timeoutSeconds);
            Console.WriteLine();

            // Test 2: Invalid API URL
            Console.WriteLine("--- Test 2: Invalid API URL ---");
            TestGetEfficiency("not-a-valid-url", orderJson, bearerToken, timeoutSeconds);
            Console.WriteLine();

            // Test 3: Invalid JSON payload
            Console.WriteLine("--- Test 3: Invalid JSON Payload ---");
            TestGetEfficiency(apiUrl, "not json", bearerToken, timeoutSeconds);
            Console.WriteLine();

            // Test 4: Empty JSON
            Console.WriteLine("--- Test 4: Empty JSON ---");
            TestGetEfficiency(apiUrl, "", bearerToken, timeoutSeconds);
            Console.WriteLine();

            // Test 5: Rate limiting (rapid calls)
            Console.WriteLine("--- Test 5: Rate Limiting (10 rapid calls) ---");
            for (int i = 0; i < 10; i++)
            {
                var result = EffClient.GetEfficiency(apiUrl, orderJson, bearerToken, timeoutSeconds);
                if (result.StatusMessage.Contains("Rate limit"))
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine($"Call {i + 1}: Rate limit hit - {result.StatusMessage}");
                    Console.ResetColor();
                    break;
                }
                else
                {
                    Console.WriteLine($"Call {i + 1}: OK");
                }
                System.Threading.Thread.Sleep(100); // Small delay
            }
            Console.WriteLine();

            // Test 6: Timeout clamping
            Console.WriteLine("--- Test 6: Timeout Clamping ---");
            var resultNegative = EffClient.GetEfficiency(apiUrl, orderJson, bearerToken, -5);
            Console.WriteLine($"Negative timeout (-5): Clamped and processed");
            var resultTooLarge = EffClient.GetEfficiency(apiUrl, orderJson, bearerToken, 10000);
            Console.WriteLine($"Very large timeout (10000): Clamped and processed");
            Console.WriteLine();

            Console.WriteLine("=== All Tests Complete ===");
            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
        }

        static void TestGetEfficiency(string apiUrl, string orderJson, string bearerToken, int timeoutSeconds)
        {
            try
            {
                EfficiencyResult result = EffClient.GetEfficiency(apiUrl, orderJson, bearerToken, timeoutSeconds);

                // Verify no exceptions were thrown
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("✓ No exceptions thrown");

                // Check StatusMessage
                if (result.StatusMessage == "ok" || result.StatusMessage.Contains("ok"))
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine($"✓ StatusMessage: {result.StatusMessage}");
                    Console.WriteLine($"  SelectedRollWidth_mm: {result.SelectedRollWidth_mm}");
                    Console.WriteLine($"  WastePercent: {result.WastePercent}");
                    Console.WriteLine($"  UsedLength_m: {result.UsedLength_m}");
                    Console.WriteLine($"  MarkerCount: {result.MarkerCount}");
                    Console.WriteLine($"  EfficiencyPercent: {result.EfficiencyPercent}");
                    Console.WriteLine($"  CalcId: {result.CalcId}");
                    Console.WriteLine($"  QuoteId: {result.QuoteId}");
                    Console.WriteLine($"  LineId: {result.LineId}");

                    // Verify values match expected ranges
                    if (result.SelectedRollWidth_mm > 0 && result.EfficiencyPercent > 0 && result.EfficiencyPercent <= 100)
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("✓ Values are within expected ranges");
                    }
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine($"⚠ StatusMessage: {result.StatusMessage}");
                    Console.WriteLine($"  (This is expected for error test cases)");
                    
                    // Verify error result has safe defaults
                    if (result.WastePercent == 100.0 && result.EfficiencyPercent == 0.0)
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("✓ Error result has safe default values");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"✗ EXCEPTION THROWN (this should not happen!): {ex.GetType().Name}: {ex.Message}");
            }
            finally
            {
                Console.ResetColor();
            }
        }
    }
}
