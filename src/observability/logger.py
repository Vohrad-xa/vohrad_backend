"""Main logging interface and utility functions."""

from .config import LoggingConfig
from .context import PerformanceTracker
import logging
from typing import Any, Dict, Optional


def setup_logging(settings: Optional[Dict[str, Any]] = None):
    """Setup logging configuration based on environment settings.

    Args:
        settings: Dictionary with logging configuration settings
    """
    if settings is None:
        settings = {}

    config_manager = LoggingConfig(settings)
    config_manager.setup()


def get_logger(name: str = "vohrad") -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name, defaults to 'vohrad'

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Get audit logger for compliance and sensitive operations.

    Returns:
        Audit logger instance
    """
    return logging.getLogger("vohrad.audit")


def get_security_logger() -> logging.Logger:
    """Get security logger for authentication and authorization events.

    Returns:
        Security logger instance
    """
    return logging.getLogger("vohrad.security")


def log_with_context(logger: logging.Logger, level: int, message: str, **extra_fields):
    """Log a message with additional context fields.

    Args:
        logger: Logger instance to use
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **extra_fields: Additional fields to include in the log
    """
    record = logger.makeRecord(logger.name, level, "<context>", 0, message, (), None)
    record.extra_fields = extra_fields
    logger.handle(record)


def get_contextual_logger(name: str = "vohrad") -> "ContextualLogger":
    """Get a logger that automatically includes context information.

    Args:
        name: Logger name, defaults to 'vohrad'

    Returns:
        ContextualLogger instance that automatically adds context
    """
    base_logger = get_logger(name)
    return ContextualLogger(base_logger)


class ContextualLogger:
    """Logger wrapper that automatically includes correlation context."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _add_context_extra(self, extra: Optional[dict] = None) -> dict:
        """Add context information to extra fields."""
        if extra is None:
            extra = {}

        # Add current context information
        context_info = PerformanceTracker.get_context_info()
        extra.update(context_info)

        return extra

    def debug(self, msg, *args, extra=None, **kwargs):
        """Log debug message with automatic context."""
        extra = self._add_context_extra(extra)
        self._logger.debug(msg, *args, extra=extra, **kwargs)

    def info(self, msg, *args, extra=None, **kwargs):
        """Log info message with automatic context."""
        extra = self._add_context_extra(extra)
        self._logger.info(msg, *args, extra=extra, **kwargs)

    def warning(self, msg, *args, extra=None, **kwargs):
        """Log warning message with automatic context."""
        extra = self._add_context_extra(extra)
        self._logger.warning(msg, *args, extra=extra, **kwargs)

    def error(self, msg, *args, extra=None, **kwargs):
        """Log error message with automatic context."""
        extra = self._add_context_extra(extra)
        self._logger.error(msg, *args, extra=extra, **kwargs)

    def critical(self, msg, *args, extra=None, **kwargs):
        """Log critical message with automatic context."""
        extra = self._add_context_extra(extra)
        self._logger.critical(msg, *args, extra=extra, **kwargs)

    def exception(self, msg, *args, extra=None, **kwargs):
        """Log exception with automatic context."""
        extra = self._add_context_extra(extra)
        self._logger.exception(msg, *args, extra=extra, **kwargs)
