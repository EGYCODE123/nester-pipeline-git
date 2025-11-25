using System.Collections.Generic;
using Newtonsoft.Json;

namespace Kvadrat.NesterBridge
{
    /// <summary>
    /// DTOs matching the exact JSON response shape from the Nester API.
    /// Used internally for deserialization.
    /// </summary>
    internal class NesterLineResultDto
    {
        [JsonProperty("line_id")]
        public string LineId { get; set; }

        [JsonProperty("waste_factor_pct")]
        public double WasteFactorPct { get; set; }

        [JsonProperty("utilization")]
        public double Utilization { get; set; }

        [JsonProperty("used_length_mm")]
        public double UsedLengthMm { get; set; }

        [JsonProperty("blind_area_m2")]
        public double BlindAreaM2 { get; set; }

        [JsonProperty("roll_area_m2")]
        public double RollAreaM2 { get; set; }

        [JsonProperty("waste_area_m2")]
        public double WasteAreaM2 { get; set; }

        [JsonProperty("roll_width_mm")]
        public double RollWidthMm { get; set; }

        [JsonProperty("pieces")]
        public int Pieces { get; set; }

        [JsonProperty("levels")]
        public int Levels { get; set; }
    }

    internal class NesterTotalsDto
    {
        [JsonProperty("eff_pct")]
        public double EffPct { get; set; }

        [JsonProperty("waste_pct")]
        public double WastePct { get; set; }

        [JsonProperty("total_area_m2")]
        public double TotalAreaM2 { get; set; }

        [JsonProperty("total_used_area_m2")]
        public double TotalUsedAreaM2 { get; set; }

        [JsonProperty("total_waste_area_m2")]
        public double TotalWasteAreaM2 { get; set; }

        [JsonProperty("total_pieces")]
        public int TotalPieces { get; set; }

        [JsonProperty("total_levels")]
        public int TotalLevels { get; set; }
    }

    internal class NesterResponseDto
    {
        [JsonProperty("calc_id")]
        public string CalcId { get; set; }

        [JsonProperty("quote_id")]
        public string QuoteId { get; set; }

        [JsonProperty("results")]
        public List<NesterLineResultDto> Results { get; set; }

        [JsonProperty("totals")]
        public NesterTotalsDto Totals { get; set; }

        [JsonProperty("version")]
        public string Version { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; }
    }
}



