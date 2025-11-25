"""
Structured logging configuration with correlation ID support.
"""
import logging
import sys
import os
from contextvars import ContextVar
from typing import Optional
from nester_api.app.core.config import get_settings


# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class CorrelationIDFilter(logging.Filter):
    """Logging filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to log record if available."""
        record.correlation_id = correlation_id.get() or "-"
        return True


def setup_logging():
    """
    Configure structured logging for the application.
    
    Creates logger named 'nester_api' with:
    - Timestamp
    - Log level
    - Correlation ID
    - Message
    """
    settings = get_settings()
    
    # Create logs directory
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("nester_api")
    logger.setLevel(getattr(logging, settings.API_LOG_LEVEL.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # File handler with rotation (using standard logging, not loguru)
    from logging.handlers import RotatingFileHandler
    log_file = os.path.join(settings.LOG_DIR, "nester_api.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Structured format: timestamp level [correlation_id] message
    log_format = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(correlation_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIDFilter()
    console_handler.addFilter(correlation_filter)
    file_handler.addFilter(correlation_filter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Initialize logger
logger = setup_logging()



