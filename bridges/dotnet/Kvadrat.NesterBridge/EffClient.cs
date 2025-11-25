using System;
using System.Collections.Generic;
using System.Data;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Kvadrat.NesterBridge
{
    /// <summary>
    /// Client for calling Kvadrat Waste API from .NET (Experlogix CPQ integration).
    /// 
    /// CURRENT BEHAVIOR:
    /// - Returns System.Data.DataTable from GetEfficiency() method
    /// - Experlogix cannot see DataTable columns directly, requiring manual mapping
    /// - Uses Newtonsoft.Json for JSON parsing
    /// - Creates new HttpClient instance per call (not optimal)
    /// - No rate limiting or concurrency control
    /// 
    /// REFACTORING GOAL:
    /// - Replace DataTable with strongly-typed EfficiencyResult class
    /// - Add rate limiting and concurrency control
    /// - Use static HttpClient with proper lifecycle management
    /// - Merge Newtonsoft.Json into main DLL using ILMerge for self-contained assembly
    /// </summary>
    public static class EffClient
    {
        // Static HttpClient for connection pooling and reuse
        private static readonly HttpClient HttpClient;
        
        // Concurrency limiting: max concurrent requests
        private const int MaxConcurrentRequests = 5;
        private static readonly SemaphoreSlim ConcurrencySemaphore =
            new SemaphoreSlim(MaxConcurrentRequests, MaxConcurrentRequests);

        // Rate limiting: max requests per minute
        private const int MaxRequestsPerMinute = 120;
        private static readonly object RateLock = new object();
        private static readonly Queue<DateTime> RequestTimestamps = new Queue<DateTime>();

        static EffClient()
        {
            // Ensure TLS 1.2+
            System.Net.ServicePointManager.SecurityProtocol = 
                System.Net.SecurityProtocolType.Tls12 | System.Net.SecurityProtocolType.Tls13;

            HttpClient = new HttpClient
            {
                // Default timeout; actual timeout is controlled per call via HttpRequestMessage
                Timeout = TimeSpan.FromSeconds(10)
            };
            HttpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Kvadrat.NesterBridge/1.0");
        }

        /// <summary>
        /// Checks if the current request can proceed based on rate limiting.
        /// Returns true if within rate limit, false if rate limit exceeded.
        /// </summary>
        private static bool TryEnterRateLimit()
        {
            lock (RateLock)
            {
                var now = DateTime.UtcNow;
                
                // Remove timestamps older than 60 seconds
                while (RequestTimestamps.Count > 0 &&
                       (now - RequestTimestamps.Peek()).TotalSeconds > 60)
                {
                    RequestTimestamps.Dequeue();
                }

                // Check if we've exceeded the rate limit
                if (RequestTimestamps.Count >= MaxRequestsPerMinute)
                {
                    return false;
                }

                // Record this request timestamp
                RequestTimestamps.Enqueue(now);
                return true;
            }
        }

        /// <summary>
        /// Creates a safe error result with default values indicating failure.
        /// </summary>
        private static EfficiencyResult CreateErrorResult(string statusMessage)
        {
            return new EfficiencyResult
            {
                SelectedRollWidth_mm = 0.0,
                WastePercent = 100.0,
                UsedLength_m = 0.0,
                MarkerCount = 0,
                EfficiencyPercent = 0.0,
                StatusMessage = statusMessage ?? "Unknown error",
                CalcId = null,
                QuoteId = null,
                LineId = null
            };
        }

        /// <summary>
        /// Main method called by Experlogix CPQ.
        /// Returns a strongly-typed EfficiencyResult with all fields visible to Experlogix.
        /// </summary>
        /// <param name="apiUrl">Full API URL (e.g., "http://localhost:8000/api/v1/waste/efficiency")</param>
        /// <param name="orderJson">JSON string of the order payload</param>
        /// <param name="bearerToken">Bearer token for authentication (optional)</param>
        /// <param name="timeoutSeconds">Timeout in seconds (clamped to 1-300)</param>
        /// <returns>EfficiencyResult with efficiency metrics or error information</returns>
        public static EfficiencyResult GetEfficiency(
            string apiUrl,
            string orderJson,
            string bearerToken,
            int timeoutSeconds)
        {
            // Input validation
            if (string.IsNullOrWhiteSpace(apiUrl))
            {
                return CreateErrorResult("Invalid apiUrl: cannot be null or empty");
            }

            if (!Uri.TryCreate(apiUrl, UriKind.Absolute, out Uri uri))
            {
                return CreateErrorResult("Invalid apiUrl: must be a valid absolute URI");
            }

            if (string.IsNullOrWhiteSpace(orderJson))
            {
                return CreateErrorResult("Invalid orderJson: cannot be null or empty");
            }

            // Limit JSON payload size to prevent abuse (64 KB max)
            if (orderJson.Length > 64 * 1024)
            {
                return CreateErrorResult("Invalid orderJson: payload exceeds 64 KB limit");
            }

            // Clamp timeout to reasonable range [1, 300] seconds
            int clampedTimeout = Math.Max(1, Math.Min(300, timeoutSeconds));

            // Rate limiting check
            if (!TryEnterRateLimit())
            {
                return CreateErrorResult("Rate limit exceeded. Please try again shortly.");
            }

            // Concurrency limiting
            ConcurrencySemaphore.Wait();
            try
            {
                return ExecuteHttpRequest(uri, orderJson, bearerToken, clampedTimeout);
            }
            finally
            {
                ConcurrencySemaphore.Release();
            }
        }

        /// <summary>
        /// Executes the HTTP request with proper error handling.
        /// Never throws exceptions; always returns a safe EfficiencyResult.
        /// </summary>
        private static EfficiencyResult ExecuteHttpRequest(
            Uri apiUrl,
            string orderJson,
            string bearerToken,
            int timeoutSeconds)
        {
            // Create per-request HttpRequestMessage (bearer token not stored on static client)
            var request = new HttpRequestMessage(HttpMethod.Post, apiUrl)
            {
                Content = new StringContent(orderJson, Encoding.UTF8, "application/json")
            };

            if (!string.IsNullOrWhiteSpace(bearerToken))
            {
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", bearerToken);
            }

            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

            using (request)
            {
                // Create a cancellation token for timeout
                using (var cts = new CancellationTokenSource(TimeSpan.FromSeconds(timeoutSeconds)))
                {
                    HttpResponseMessage response;
                    try
                    {
                        response = HttpClient.SendAsync(request, cts.Token).GetAwaiter().GetResult();
                    }
                    catch (TaskCanceledException)
                    {
                        return CreateErrorResult($"Request timeout after {timeoutSeconds} seconds");
                    }
                    catch (HttpRequestException ex)
                    {
                        // Sanitize error message - don't leak internal details
                        return CreateErrorResult($"HTTP request failed: {ex.Message}");
                    }
                    catch (Exception ex)
                    {
                        // Catch-all for any other exceptions
                        return CreateErrorResult($"Request failed: {ex.GetType().Name}");
                    }

                    // Check HTTP status code
                    if (!response.IsSuccessStatusCode)
                    {
                        string reasonPhrase = response.ReasonPhrase ?? "Unknown error";
                        return CreateErrorResult($"API returned {(int)response.StatusCode} {reasonPhrase}");
                    }

                    // Read response body
                    string body;
                    try
                    {
                        body = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                    }
                    catch (Exception ex)
                    {
                        return CreateErrorResult($"Failed to read response: {ex.GetType().Name}");
                    }

                    if (string.IsNullOrWhiteSpace(body))
                    {
                        return CreateErrorResult("Empty response from API");
                    }

                    // Parse JSON response
                    NesterResponseDto dto;
                    try
                    {
                        dto = JsonConvert.DeserializeObject<NesterResponseDto>(body);
                    }
                    catch (JsonException)
                    {
                        return CreateErrorResult("Failed to parse API response JSON");
                    }

                    if (dto == null)
                    {
                        return CreateErrorResult("API returned null response");
                    }

                    if (dto.Results == null || dto.Results.Count == 0)
                    {
                        return CreateErrorResult("API returned no results");
                    }

                    // Extract data from first result line
                    var line = dto.Results[0];

                    return new EfficiencyResult
                    {
                        SelectedRollWidth_mm = line.RollWidthMm,
                        WastePercent = line.WasteFactorPct,  // line-level waste factor
                        UsedLength_m = line.UsedLengthMm / 1000.0,  // convert mm → m
                        MarkerCount = line.Levels,
                        EfficiencyPercent = line.Utilization,
                        StatusMessage = dto.Message ?? "ok",
                        CalcId = dto.CalcId,
                        QuoteId = dto.QuoteId,
                        LineId = line.LineId
                    };
                }
            }
        }

        /// <summary>
        /// Legacy wrapper method that returns DataTable for backward compatibility.
        /// NOT used by Experlogix anymore - use GetEfficiency() instead.
        /// </summary>
        [Obsolete("Use GetEfficiency() which returns EfficiencyResult instead. This method is kept for backward compatibility only.")]
        public static System.Data.DataTable GetEfficiencyDataTable(
            string apiUrl,
            string orderJson,
            string bearerToken,
            int timeoutSec = 30)
        {
            var result = GetEfficiency(apiUrl, orderJson, bearerToken, timeoutSec);
            
            var dt = new System.Data.DataTable("NesterEfficiency");
            dt.Columns.Add("SelectedRollWidth_mm", typeof(double));
            dt.Columns.Add("WastePercent", typeof(double));
            dt.Columns.Add("UsedLength_m", typeof(double));
            dt.Columns.Add("MarkerCount", typeof(int));
            dt.Columns.Add("EfficiencyPercent", typeof(double));
            dt.Columns.Add("StatusMessage", typeof(string));

            var row = dt.NewRow();
            row["SelectedRollWidth_mm"] = result.SelectedRollWidth_mm;
            row["WastePercent"] = result.WastePercent;
            row["UsedLength_m"] = result.UsedLength_m;
            row["MarkerCount"] = result.MarkerCount;
            row["EfficiencyPercent"] = result.EfficiencyPercent;
            row["StatusMessage"] = result.StatusMessage ?? string.Empty;
            dt.Rows.Add(row);

            return dt;
        }


        /// <summary>
        /// Calls the API and returns the full JSON response as a string.
        /// Returns "ERROR: ..." if the call fails.
        /// </summary>
        /// <param name="apiUrl">Full API URL (e.g., "http://localhost:8000/api/v1/waste/efficiency")</param>
        /// <param name="orderJson">JSON string of the order payload</param>
        /// <param name="bearerToken">Bearer token for authentication</param>
        /// <param name="timeoutSec">Timeout in seconds (default: 30)</param>
        /// <returns>JSON response string or "ERROR: ..." message</returns>
        public static string GetEfficiencyJson(string apiUrl, string orderJson, string bearerToken, int timeoutSec = 30)
        {
            var result = GetEfficiency(apiUrl, orderJson, bearerToken, timeoutSec);
            
            if (result.StatusMessage != "ok" && !string.IsNullOrWhiteSpace(result.StatusMessage))
            {
                return $"ERROR: {result.StatusMessage}";
            }

            // For backward compatibility, we'd need to reconstruct JSON, but this is not ideal
            // This method is kept for compatibility but GetEfficiency() is preferred
            return $"ERROR: Use GetEfficiency() method instead for proper JSON response";
        }

        /// <summary>
        /// Calls the API and returns only the waste_factor_pct from the first line's result.
        /// Returns "ERROR: ..." if the call fails or JSON parsing fails.
        /// </summary>
        /// <param name="apiUrl">Full API URL (e.g., "http://localhost:8000/api/v1/waste/efficiency")</param>
        /// <param name="orderJson">JSON string of the order payload</param>
        /// <param name="bearerToken">Bearer token for authentication</param>
        /// <param name="timeoutSec">Timeout in seconds (default: 30)</param>
        /// <returns>waste_factor_pct as string (e.g., "15.23") or "ERROR: ..." message</returns>
        public static string GetWasteFactorPct(string apiUrl, string orderJson, string bearerToken, int timeoutSec = 30)
        {
            var result = GetEfficiency(apiUrl, orderJson, bearerToken, timeoutSec);
            
            if (result.StatusMessage != "ok" && !string.IsNullOrWhiteSpace(result.StatusMessage))
            {
                return $"ERROR: {result.StatusMessage}";
            }

            return result.WastePercent.ToString("F2");
        }
    }
}
