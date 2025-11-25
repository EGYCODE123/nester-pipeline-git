"""
Pydantic models for API response bodies.
"""
from pydantic import BaseModel
from typing import List


class LineResult(BaseModel):
    """Result for a single line."""
    line_id: str
    waste_factor_pct: float
    utilization: float
    used_length_mm: float
    blind_area_m2: float
    roll_area_m2: float
    waste_area_m2: float
    roll_width_mm: int
    pieces: int
    levels: int


class TotalsResult(BaseModel):
    """Aggregated totals across all lines."""
    eff_pct: float
    waste_pct: float
    total_area_m2: float
    total_used_area_m2: float
    total_waste_area_m2: float
    total_pieces: int
    total_levels: int


class EfficiencyResponse(BaseModel):
    """
    Response body for waste efficiency calculation.
    
    Matches the existing API contract exactly.
    """
    calc_id: str
    quote_id: str
    results: List[LineResult]
    totals: TotalsResult
    version: str
    message: str



