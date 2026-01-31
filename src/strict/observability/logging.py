import structlog
import logging
import sys
from typing import Any
from strict.config import settings


def configure_logging():
    """Configure structured logging."""

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.debug:
        # Development logging (colorful, human-readable)
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        # Production logging (JSON)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to intercept Uvicorn/FastAPI logs
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    # Redirect standard logging to structlog
    # (Implementation omitted for brevity, but standard practice in prod)


logger = structlog.get_logger()


def get_logger(name: str | None = None) -> Any:
    """Get a structured logger."""
    return structlog.get_logger(name)
