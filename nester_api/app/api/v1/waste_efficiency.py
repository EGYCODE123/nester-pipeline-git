"""
Waste efficiency calculation endpoint.
"""
import time
from fastapi import APIRouter, Depends, Request, HTTPException, Body
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from nester_api.app.models.requests import EfficiencyRequest
from nester_api.app.models.responses import EfficiencyResponse
from nester_api.app.core.security import get_api_key
from nester_api.app.core.engine_client import compute_efficiency_wrapper
from nester_api.app.core.logging import logger
from nester_api.app.core.config import get_settings
from nester_api.app.core.rate_limit import get_rate_limit_key


router = APIRouter()
settings = get_settings()

# Create limiter instance for this router
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://"
)

# Default example for request body
REQUEST_BODY_EXAMPLE = {
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


@router.post("/api/v1/waste/efficiency", response_model=EfficiencyResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def efficiency(
    request: Request,
    req: EfficiencyRequest = Body(..., example=REQUEST_BODY_EXAMPLE),
    _: str = Depends(get_api_key)
) -> EfficiencyResponse:
    """
    Calculate waste efficiency for a quote.
    
    Requires authentication via X-API-Key header.
    Rate limited to 60 requests per minute per client.
    
    Args:
        request: FastAPI request object (for rate limiting)
        req: EfficiencyRequest with quote_id, model, available_widths_mm, lines
        
    Returns:
        EfficiencyResponse with calc_id, quote_id, results, totals, version, message
        
    Raises:
        HTTPException(400) if validation fails
        HTTPException(401) if authentication fails
        HTTPException(429) if rate limit exceeded
        HTTPException(500) on server error
    """
    start_time = time.perf_counter()
    corr_id = request.state.correlation_id
    
    try:
        logger.info(
            f"Request started: calc_id=..., quote_id={req.quote_id}, "
            f"lines={len(req.lines)}, available_widths={req.available_widths_mm}, "
            f"correlation_id={corr_id}"
        )
        
        # Validate line count
        if len(req.lines) > 1000:
            raise HTTPException(
                status_code=400,
                detail={"error": "bad_request", "details": "Maximum 1000 lines allowed per request"}
            )
        
        # Compute efficiency
        response = compute_efficiency_wrapper(req)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"Request completed: calc_id={response.calc_id}, quote_id={req.quote_id}, "
            f"duration={duration_ms:.2f}ms, status=success, correlation_id={corr_id}"
        )
        
        return response
        
    except HTTPException:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"Request failed: quote_id={req.quote_id}, "
            f"duration={duration_ms:.2f}ms, status=error, correlation_id={corr_id}",
            exc_info=True
        )
        raise
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            f"Request error: quote_id={req.quote_id}, "
            f"duration={duration_ms:.2f}ms, error={str(e)}, correlation_id={corr_id}"
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "server_error", "details": str(e)}
        )

