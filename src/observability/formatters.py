"""Log formatters for different output formats and environments."""

from .context import correlation_id_var, request_start_time_var, tenant_id_var, user_id_var
from datetime import datetime, timezone
import json
import logging
import os
import time
import typing


class ColoredConsoleFormatter(logging.Formatter):
    """Colored formatter for development console output with clear visual distinction."""

    COLORS: typing.ClassVar[dict[str, str]] = {
        "DEBUG"   : "\033[36m",  # Cyan - for debugging info
        "INFO"    : "\033[32m",  # Green - for normal operations
        "WARNING" : "\033[33m",  # Yellow - for warnings
        "ERROR"   : "\033[31m",  # Red - for errors
        "CRITICAL": "\033[35m",  # Magenta - for critical issues
    }
    RESET: typing.ClassVar[str] = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and correlation context."""
        if record.levelname in self.COLORS:
            colored_level = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        else:
            colored_level = record.levelname

        correlation_id = correlation_id_var.get()
        correlation_part = f"[{correlation_id[:8]}]" if correlation_id else ""
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        message = f"[{timestamp}] {correlation_part} {colored_level:<8s} {record.name} - {record.getMessage()}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class EnterpriseJSONFormatter(logging.Formatter):
    """JSON formatter with enterprise fields for production environments."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hostname     = os.getenv("HOSTNAME", "localhost")
        self.service_name = os.getenv("SERVICE_NAME", "vohrad-api")
        self.environment  = os.getenv("ENVIRONMENT", "development")
        self.version      = os.getenv("APP_VERSION", "1.0.0")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON with enterprise metadata."""
        log_data = {
            "@timestamp" : datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "service"    : self.service_name,
            "version"    : self.version,
            "environment": self.environment,
            "hostname"   : self.hostname,
            "level"      : record.levelname,
            "logger"     : record.name,
            "message"    : record.getMessage(),
            "module"     : record.module,
            "function"   : record.funcName,
            "line"       : record.lineno,
            "thread_id"  : record.thread,
            "process_id" : record.process,
        }

        if correlation_id := correlation_id_var.get():
            log_data["correlation_id"] = correlation_id

        if user_id := user_id_var.get():
            log_data["user_id"] = user_id

        if tenant_id := tenant_id_var.get():
            log_data["tenant_id"] = tenant_id

        if start_time := request_start_time_var.get():
            log_data["request_duration_ms"] = round((time.time() - start_time) * 1000, 2)

        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        if record.exc_info:
            log_data["exception"] = {
                "class"    : record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message"  : str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False)


class DetailedFileFormatter(logging.Formatter):
    """Detailed formatter for file logging with function and line info."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format_string = "[%(asctime)s] [%(name)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(funcName)s() - %(message)s"
        self.date_format = "%Y-%m-%dT%H:%M:%S%z"

    def format(self, record: logging.LogRecord) -> str:
        """Format with detailed context information."""
        formatter = logging.Formatter(self.format_string, self.date_format)
        return formatter.format(record)
