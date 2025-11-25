# app.py
import os
import uuid
import time
from typing import Optional, List
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, conint, Field, validator
from loguru import logger
from nester.settings import API_TOKEN, LOG_DIR
from nester.engine.core import Line, compute_efficiency

# Configure logging
os.makedirs(LOG_DIR, exist_ok=True)
logger.add(
    os.path.join(LOG_DIR, "waste_api_{time}.log"),
    rotation="10 MB",
    retention=10,  # Keep 10 files
    enqueue=True
)

DEV = os.getenv("NEST_ENV", "dev") == "dev"
API_KEY = API_TOKEN  # Use API_TOKEN from settings

async def require_auth(authorization: str | None = Header(None)):
    if DEV:
        return
    if not authorization:
        raise HTTPException(401, {"error":"unauthorized","details":"Missing Authorization header"})
    token = authorization.split(" ",1)[1] if authorization.startswith("Bearer ") else authorization
    if token != API_KEY:
        raise HTTPException(401, {"error":"unauthorized","details":"Invalid token"})

def bad_request(msg: str):
    """Helper to format bad request errors."""
    raise HTTPException(status_code=400, detail={"error": "bad_request", "details": msg})

class LineIn(BaseModel):
    line_id: str
    width_mm: conint(gt=0)
    drop_mm: conint(gt=0)
    qty: conint(gt=0)
    fabric_code: str | None = None
    series: str | None = None

class Req(BaseModel):
    quote_id: str
    model: str = Field(pattern="^(blinds|header)$")
    available_widths_mm: Optional[List[conint(gt=0)]] = None
    lines: list[LineIn]
    
    @validator("available_widths_mm")
    def _normalize_widths(cls, v):
        if v is None:
            return v
        # Remove duplicates while preserving order, then sort
        v = list(dict.fromkeys(v))
        return sorted(v)

app = FastAPI(title="Kvadrat Waste API", version="1.0.0")

@app.get("/health")
def health(): 
    return {"status": "ok", "version": app.version}

@app.post("/api/v1/waste/efficiency")
def efficiency(req: Req, _=Depends(require_auth)):
    calc_id = uuid.uuid4().hex[:8]
    start_time = time.perf_counter()
    status = "success"
    
    try:
        logger.info(f"Request started: calc_id={calc_id}, quote_id={req.quote_id}, lines={len(req.lines)}, available_widths={req.available_widths_mm}")
        
        if len(req.lines) > 1000:
            bad_request("Maximum 1000 lines allowed per request")
        
        # Convert LineIn to Line objects
        lines = [Line(**l.model_dump()) for l in req.lines]
        
        # Call compute_efficiency with candidate_widths_mm
        results, totals = compute_efficiency(lines, candidate_widths_mm=req.available_widths_mm)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        response = {
            "calc_id": calc_id,
            "quote_id": req.quote_id,
            "results": results,
            "totals": totals,
            "version": app.version,
            "message": "ok",
        }
        
        logger.info(
            f"Request completed: calc_id={calc_id}, quote_id={req.quote_id}, "
            f"duration={duration_ms:.2f}ms, status={status}"
        )
        
        return response
        
    except HTTPException:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status = "error"
        logger.error(
            f"Request failed: calc_id={calc_id}, quote_id={req.quote_id}, "
            f"duration={duration_ms:.2f}ms, status={status}"
        )
        raise
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status = "error"
        logger.exception(
            f"Request error: calc_id={calc_id}, quote_id={req.quote_id}, "
            f"duration={duration_ms:.2f}ms, error={str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "server_error", "details": str(e)}
        )

@app.get("/")
def root():
    return {
        "service": "Kvadrat Waste API",
        "docs": "/docs",
        "health": "/health"
    }
