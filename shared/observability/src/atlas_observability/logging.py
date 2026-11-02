"""Structured logging configuration for ATLAS services."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from atlas_observability.context import get_correlation_id


class CorrelationFilter(logging.Filter):
    """Logging filter that injects correlation_id and service_name into the LogRecord."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        record.service_name = self.service_name
        return True


class JsonFormatter(logging.Formatter):
    """Format logs as compact, single-line JSON records."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service_name", "unknown"),
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Format logs as clean, human-readable lines for local console output."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        corr = getattr(record, "correlation_id", "-")
        service = getattr(record, "service_name", "atlas")
        corr_str = f" [corr:{corr}]" if corr != "-" else ""
        base = f"[{timestamp}] [{record.levelname:<5}] [{service}]{corr_str} {record.name}: {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: str = "console",
) -> logging.Logger:
    """Configure the root logger with the specified format and correlation filtering."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove existing handlers to prevent duplicates during testing or reloads
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.addFilter(CorrelationFilter(service_name=service_name))

    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root.addHandler(handler)

    # Quiet overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger(service_name)
    logger.info(
        "Structured logging initialized for service '%s' (level=%s, format=%s)",
        service_name,
        log_level,
        log_format,
    )
    return logger
