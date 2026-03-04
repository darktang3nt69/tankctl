"""
Structured logging utilities for TankCtl.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

from src.config.settings import settings


class StructuredLogger:
    """Structured logging for TankCtl backend."""

    def __init__(self, name: str) -> None:
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(settings.log_level)

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(
        self,
        level: int,
        event: str,
        device_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log structured message."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
        }

        if device_id:
            log_data["device_id"] = device_id

        log_data.update(metadata)

        message = json.dumps(log_data)
        self.logger.log(level, message)

    def info(
        self,
        event: str,
        device_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log info level event."""
        self._log(logging.INFO, event, device_id, **metadata)

    def warning(
        self,
        event: str,
        device_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log warning level event."""
        self._log(logging.WARNING, event, device_id, **metadata)

    def error(
        self,
        event: str,
        device_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log error level event."""
        self._log(logging.ERROR, event, device_id, **metadata)

    def debug(
        self,
        event: str,
        device_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Log debug level event."""
        self._log(logging.DEBUG, event, device_id, **metadata)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
