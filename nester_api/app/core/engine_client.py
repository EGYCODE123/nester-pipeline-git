"""
Engine client wrapper for the existing compute_efficiency function.
"""
from typing import List, Dict, Any
from nester.engine.core import Line, compute_efficiency
from nester_api.app.models.requests import EfficiencyRequest
from nester_api.app.models.responses import EfficiencyResponse, LineResult, TotalsResult


def compute_efficiency_wrapper(request: EfficiencyRequest) -> EfficiencyResponse:
    """
    Wrapper around the existing compute_efficiency function.
    
    Converts Pydantic request model to engine Line objects,
    calls compute_efficiency, and converts results back to response model.
    
    Args:
        request: EfficiencyRequest with quote_id, model, available_widths_mm, lines
        
    Returns:
        EfficiencyResponse with calc_id, quote_id, results, totals, version, message
    """
    # Convert request lines to engine Line objects
    lines = [
        Line(
            line_id=line.line_id,
            width_mm=line.width_mm,
            drop_mm=line.drop_mm,
            qty=line.qty,
            fabric_code=line.fabric_code,
            series=line.series
        )
        for line in request.lines
    ]
    
    # Call existing compute_efficiency function
    results_data, totals_data = compute_efficiency(
        lines,
        candidate_widths_mm=request.available_widths_mm
    )
    
    # Convert results to response models
    line_results = [
        LineResult(**result) for result in results_data
    ]
    
    totals = TotalsResult(**totals_data)
    
    # Generate calc_id (8-character hex)
    import uuid
    calc_id = uuid.uuid4().hex[:8]
    
    # Build response
    return EfficiencyResponse(
        calc_id=calc_id,
        quote_id=request.quote_id,
        results=line_results,
        totals=totals,
        version="1.0.0",
        message="ok"
    )



