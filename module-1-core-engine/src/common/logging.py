# Логирование

import logging
import sys
import json
import uuid
from contextvars import ContextVar


# Context var for correlation ID
_correlation_id: ContextVar[str] = ContextVar(
    "correlation_id", default=str(uuid.uuid4())
)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID."""
    _correlation_id.set(correlation_id)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging with JSON formatter."""
    logger = logging.getLogger("chameleon")
    logger.setLevel(getattr(logging, level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger


# Create default logger
logger = setup_logging()


# Helper functions for structured logging
def log_info(message: str, **kwargs):
    """Log INFO level with extra fields."""
    logger.info(message, extra={"extra_fields": kwargs})


def log_error(message: str, **kwargs):
    """Log ERROR level with extra fields."""
    logger.error(message, extra={"extra_fields": kwargs})


def log_warning(message: str, **kwargs):
    """Log WARNING level with extra fields."""
    logger.warning(message, extra={"extra_fields": kwargs})


def log_debug(message: str, **kwargs):
    """Log DEBUG level with extra fields."""
    logger.debug(message, extra={"extra_fields": kwargs})
