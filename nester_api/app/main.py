"""
FastAPI application factory.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from nester_api.app.core.config import get_settings
from nester_api.app.core.logging import setup_logging
from nester_api.app.core.rate_limit import get_rate_limit_key
from nester_api.app.middleware.correlation_id import CorrelationIDMiddleware
from nester_api.app.api.v1.waste_efficiency import router as waste_efficiency_router
from nester_api.app.health.routes import router as health_router


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    settings = get_settings()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Initializing Nester API application")
    
    # Create FastAPI app
    app = FastAPI(
        title="Kvadrat Waste API",
        version="1.0.0",
        description="Enterprise-grade waste efficiency calculation service",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS
    if settings.API_ALLOWED_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.API_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add correlation ID middleware
    app.add_middleware(CorrelationIDMiddleware)
    
    # Initialize rate limiter (shared across app)
    limiter = Limiter(
        key_func=get_rate_limit_key,
        default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
        storage_uri="memory://"
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Include routers
    app.include_router(waste_efficiency_router)
    app.include_router(health_router)
    
    # Root endpoint
    @app.get("/")
    def root():
        return {
            "service": "Kvadrat Waste API",
            "version": app.version,
            "docs": "/docs",
            "health": "/health/live"
        }
    
    logger.info("Application initialized successfully")
    
    return app


# Create app instance for uvicorn
app = create_app()

