"""
Entry point for running the API as a module: python -m nester_api
"""
import uvicorn
from nester_api.app.core.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "nester_api.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.API_LOG_LEVEL.lower()
    )



