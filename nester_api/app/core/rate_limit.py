"""
Rate limiting using slowapi.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Callable, Tuple
from nester_api.app.core.config import get_settings


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key from client IP and API key.
    
    Uses (client_ip, api_key) tuple for per-client-per-key limiting.
    """
    client_ip = get_remote_address(request)
    
    # Try to extract API key from request
    api_key = "anonymous"
    api_key_header = request.headers.get("X-API-Key", "")
    if api_key_header:
        api_key = api_key_header[:8]  # Use first 8 chars for key
    
    return f"{client_ip}:{api_key}"


# Initialize limiter
settings = get_settings()
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://"
)


# Note: Rate limit exceeded handler is configured in main.py
# using slowapi's default _rate_limit_exceeded_handler



