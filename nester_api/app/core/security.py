"""
Security module for API authentication.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from .config import get_settings

api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API Key for authentication. Get your API key from your administrator."
)

def get_api_key(api_key: str = Security(api_key_scheme)) -> str:
    settings = get_settings()
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "details": "Missing Authorization header or X-API-Key",
            },
        )
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "details": "Invalid API key",
            },
        )
    return api_key

