"""Log filters for noise reduction and smart filtering."""

import logging
from typing import ClassVar
from typing import List


class SmartFilter(logging.Filter):
    """Smart filter to reduce noise from infrastructure and development logs."""

    NOISE_PATTERNS: ClassVar[List[str]] = [
        "GET /health",
        "GET /metrics",
        "GET /status",
        "GET /ping",
        "GET /static/",
        "GET /favicon.ico",
        "GET /robots.txt",
        "GET /docs",
        "GET /redoc",
        "GET /openapi.json",
    ]

    UVICORN_NOISE: ClassVar[List[str]] = [
        "Application startup complete",
        "Application shutdown complete",
        "Started server process",
        "Waiting for application startup",
        "Waiting for application shutdown",
        "Finished server process",
        "Shutting down",
        "shutdown()",
        "Application starting up",
        "Application shutting down",
    ]

    def __init__(self, filter_for_files: bool = False):
        """Initialize the SmartFilter.

        Args:
            filter_for_files: If True, also filters request logs from file handlers
        """
        super().__init__()
        self.filter_for_files = filter_for_files

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to reduce infrastructure noise and optionally filter request logs from files."""
        message = record.getMessage()

        if record.levelno >= logging.ERROR:
            return True

        if record.levelno >= logging.WARNING:
            return True

        if self.filter_for_files and record.levelno == logging.INFO:
            if record.name == "vohrad.requests":
                if "Request completed" in message or "Request started" in message:
                    return False

        if record.levelno <= logging.INFO:
            for pattern in self.NOISE_PATTERNS:
                if pattern in message:
                    return False

        if record.name.startswith("uvicorn") and record.levelno <= logging.INFO:
            for noise in self.UVICORN_NOISE:
                if noise in message:
                    return False

        if record.name.startswith("vohrad.startup") and record.levelno <= logging.INFO:
            startup_noise = ["Application starting up", "Application shutting down"]
            for noise in startup_noise:
                if noise in message:
                    return False

        return True


class LevelFilter(logging.Filter):
    """Filter that only allows specific log levels."""

    def __init__(self, min_level: int = logging.NOTSET, max_level: int = logging.CRITICAL):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter based on log level range."""
        return self.min_level <= record.levelno <= self.max_level


class ModuleFilter(logging.Filter):
    """Filter that allows or blocks specific modules."""

    def __init__(self, allowed_modules: List[str] | None = None, blocked_modules: List[str] | None = None):
        super().__init__()
        self.allowed_modules = allowed_modules or []
        self.blocked_modules = blocked_modules or []

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter based on module names."""
        # If allowed modules specified, only allow those
        if self.allowed_modules:
            return any(record.name.startswith(module) for module in self.allowed_modules)

        # If blocked modules specified, block those
        if self.blocked_modules:
            return not any(record.name.startswith(module) for module in self.blocked_modules)

        return True
