"""
Logging configuration for the Lead Management System.
Uses structlog for structured logging with JSON output.
"""

import logging
import sys
from typing import Any, Dict

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    """
    if not STRUCTLOG_AVAILABLE:
        # Fallback to basic logging if structlog is not available
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
        )
        return

    # Configure structlog
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json":
        # JSON logging for production
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable logging for development
        shared_processors.append(
            structlog.dev.ConsoleRenderer(colors=settings.DEBUG)
        )

    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper())

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handler for structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)