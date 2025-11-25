"""
Pydantic models for API request bodies.
"""
from pydantic import BaseModel, Field, validator, conint
from typing import List, Optional


class LineIn(BaseModel):
    """Single line item in the efficiency calculation request."""
    line_id: str
    width_mm: conint(gt=0)
    drop_mm: conint(gt=0)
    qty: conint(gt=0)
    fabric_code: Optional[str] = None
    series: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "line_id": "L1",
                "width_mm": 2300,
                "drop_mm": 2100,
                "qty": 2,
                "fabric_code": "FAB001",
                "series": "SERIES-A"
            }
        }


class EfficiencyRequest(BaseModel):
    """
    Request body for waste efficiency calculation.
    
    Matches the existing API contract exactly.
    """
    quote_id: str
    model: str = Field(pattern="^(blinds|header)$")
    available_widths_mm: Optional[List[conint(gt=0)]] = None
    lines: List[LineIn]
    
    @validator("available_widths_mm")
    def _normalize_widths(cls, v):
        """Remove duplicates and sort widths."""
        if v is None:
            return v
        # Remove duplicates while preserving order, then sort
        v = list(dict.fromkeys(v))
        return sorted(v)
    
    class Config:
        schema_extra = {
            "example": {
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
        }



