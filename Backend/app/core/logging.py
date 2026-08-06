"""Base logging configuration for the application."""

import logging
import sys

from app.core.config import settings

_configured = False

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure the root logger once for the whole process."""
    global _configured
    if _configured:
        return

    logging.basicConfig(
        level=settings.log_level.upper(),
        format=_LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Reduce noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger initialized with the base configuration."""
    setup_logging()
    return logging.getLogger(name)
