"""
Structured Logging Utilities

Provides structlog-backed logging with automatic JSON formatting.
Integrates with the existing logging infrastructure.

Usage:
    from src.utils.log_utils import get_logger, structlog

    logger = get_logger(__name__)
    logger.info("request_processed", user_id=123, duration_ms=45)

    # Output: {"event": "request_processed", "user_id": 123, "duration_ms": 45, "timestamp": "..."}
"""

import logging
import sys
from typing import Any

try:
    import structlog

    def configure_structlog(log_level: str = "INFO") -> None:
        """Configure structlog with proper processors."""
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper(), logging.INFO),
        )

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def get_logger(name: str) -> Any:
        """Get a structlog logger instance."""
        return structlog.get_logger(name)

    # Pre-configure structlog
    configure_structlog()

except ImportError:

    def configure_structlog(log_level: str = "INFO") -> None:
        """Fallback to stdlib logging if structlog not available."""
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
        )

    def get_logger(name: str) -> logging.Logger:
        """Get a standard logging logger instance."""
        return logging.getLogger(name)

    class MockStructlog:
        """Mock structlog for compatibility."""

        def __init__(self, logger: logging.Logger):
            self._logger = logger

        def info(self, msg: str, **kwargs: Any) -> None:
            self._logger.info(msg, extra=kwargs)

        def warning(self, msg: str, **kwargs: Any) -> None:
            self._logger.warning(msg, extra=kwargs)

        def error(self, msg: str, **kwargs: Any) -> None:
            self._logger.exception(msg, extra=kwargs)

        def debug(self, msg: str, **kwargs: Any) -> None:
            self._logger.debug(msg, extra=kwargs)
