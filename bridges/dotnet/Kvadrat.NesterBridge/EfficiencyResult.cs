namespace Kvadrat.NesterBridge
{
    /// <summary>
    /// Strongly-typed result object returned by GetEfficiency() method.
    /// All properties are public with get/set so Experlogix can reflect them directly.
    /// </summary>
    public class EfficiencyResult
    {
        public double SelectedRollWidth_mm { get; set; }
        public double WastePercent { get; set; }
        public double UsedLength_m { get; set; }
        public int MarkerCount { get; set; }
        public double EfficiencyPercent { get; set; }
        public string StatusMessage { get; set; }

        public string CalcId { get; set; }
        public string QuoteId { get; set; }
        public string LineId { get; set; }
    }
}



