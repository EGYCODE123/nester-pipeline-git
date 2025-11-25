"""
Health check endpoints.
"""
from fastapi import APIRouter
from typing import Dict


router = APIRouter()


@router.get("/health/live")
async def health_live() -> Dict[str, str]:
    """
    Liveness probe endpoint.
    
    Returns 200 OK if the process is running.
    No authentication required.
    """
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready() -> Dict[str, str]:
    """
    Readiness probe endpoint.
    
    Returns 200 OK if the application is initialized and ready to serve requests.
    Checks that the engine module can be imported.
    No authentication required.
    """
    try:
        # Verify engine can be imported
        from nester.engine.core import compute_efficiency
        return {"status": "ok"}
    except Exception as e:
        # If engine import fails, return 503
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "error": str(e)}
        )



