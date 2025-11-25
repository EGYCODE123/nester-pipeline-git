"""
Correlation ID middleware for request tracing.
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from nester_api.app.core.logging import correlation_id


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and manage correlation IDs for each request.
    
    - Generates UUID if not present in X-Correlation-ID header
    - Stores in request state
    - Adds to response header
    - Sets in context variable for logging
    """
    
    async def dispatch(self, request: Request, call_next):
        # Check for existing correlation ID in header
        corr_id = request.headers.get("X-Correlation-ID")
        
        if not corr_id:
            # Generate new UUID
            corr_id = str(uuid.uuid4())
        
        # Store in request state
        request.state.correlation_id = corr_id
        
        # Set in context variable for logging
        correlation_id.set(corr_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response header
        response.headers["X-Correlation-ID"] = corr_id
        
        return response



