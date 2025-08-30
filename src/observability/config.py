"""Logging configuration and setup for different environments."""

import logging
import logging.config
from .filters import SmartFilter
from pathlib import Path
from typing import Any
from typing import Dict


class LoggingConfig:
    """Clean logging configuration manager for different environments."""
    def __init__(self, settings: Dict[str, Any]):
        self.settings    = settings
        self.environment = settings.get("ENVIRONMENT", "development")
        self.log_level   = settings.get("LOG_LEVEL", "INFO")
        self.log_dir     = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

    def setup(self):
        """Setup logging based on environment with appropriate configuration."""
        config = self._build_config()
        logging.config.dictConfig(config)
        self._apply_smart_filters()

    def _build_config(self) -> Dict[str, Any]:
        """Build logging configuration based on environment."""
        if self.environment == "production":
            return self._production_config()
        elif self.environment == "testing":
            return self._testing_config()
        else:
            return self._development_config()

    def _base_config(self) -> Dict[str, Any]:
        """Base configuration shared across all environments."""
        return {
            "version"                 : 1,
            "disable_existing_loggers": False,
            "formatters"              : {
                "colored": {"()": "observability.formatters.ColoredConsoleFormatter"},
                "simple" : {
                    "format" : "[%(asctime)s] [%(name)s] %(levelname)-8s %(message)s",
                    "datefmt": "%H:%M:%S",
                },
                "detailed": {"()": "observability.formatters.DetailedFileFormatter"},
                "json"    : {"()": "observability.formatters.EnterpriseJSONFormatter"},
            },
            "filters": {
                "smart_filter"          : {"()": "observability.filters.SmartFilter"},
                "smart_filter_for_files": {"()": "observability.filters.SmartFilter", "filter_for_files": True},
            },
        }

    def _development_config(self) -> Dict[str, Any]:
        """Development environment configuration - colored console + detailed files."""
        config = self._base_config()

        config.update(
            {
                "handlers": {
                    "console": {
                        "class"    : "logging.StreamHandler",
                        "level"    : "DEBUG",
                        "formatter": "colored",
                        "stream"   : "ext://sys.stdout",
                        "filters"  : ["smart_filter"],
                    },
                    "file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "INFO",
                        "formatter"  : "detailed",
                        "filename"   : str(self.log_dir / "app.log"),
                        "maxBytes"   : 10485760,
                        "backupCount": 5,
                        "encoding"   : "utf8",
                        "filters"    : ["smart_filter_for_files"],
                    },
                    "audit_file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "INFO",
                        "formatter"  : "detailed",
                        "filename"   : str(self.log_dir / "audit.log"),
                        "maxBytes"   : 10485760,
                        "backupCount": 5,
                        "encoding"   : "utf8",
                        "filters"    : ["smart_filter_for_files"],
                    },
                    "security_file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "INFO",
                        "formatter"  : "detailed",
                        "filename"   : str(self.log_dir / "security.log"),
                        "maxBytes"   : 10485760,
                        "backupCount": 5,
                        "encoding"   : "utf8",
                        "filters"    : ["smart_filter_for_files"],
                    },
                },
                "loggers": {
                    "root"           : {"level": "WARNING", "handlers": ["console"]},
                    "vohrad"         : {"level": self.log_level, "handlers": ["console", "file"], "propagate": False},
                    "vohrad.audit"   : {"level": "INFO", "handlers": ["audit_file"], "propagate": False},
                    "vohrad.security": {"level": "INFO", "handlers": ["security_file"], "propagate": False},
                    "uvicorn.error"  : {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
                    "uvicorn.access" : {"level": "WARNING", "handlers": ["file"], "propagate": False},
                },
            }
        )

        return config

    def _production_config(self) -> Dict[str, Any]:
        """Production environment configuration - JSON structured logs."""
        config = self._base_config()

        config.update(
            {
                "handlers": {
                    "console": {
                        "class"    : "logging.StreamHandler",
                        "level"    : "WARNING",
                        "formatter": "json",
                        "stream"   : "ext://sys.stdout",
                        "filters"  : ["smart_filter"],
                    },
                    "file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "INFO",
                        "formatter"  : "json",
                        "filename"   : str(self.log_dir / "app.log"),
                        "maxBytes"   : 52428800,
                        "backupCount": 20,
                        "encoding"   : "utf8",
                        "filters"    : ["smart_filter_for_files"],
                    },
                    "error_file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "ERROR",
                        "formatter"  : "json",
                        "filename"   : str(self.log_dir / "error.log"),
                        "maxBytes"   : 26214400,
                        "backupCount": 10,
                        "encoding"   : "utf8",
                    },
                    "audit_file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "INFO",
                        "formatter"  : "json",
                        "filename"   : str(self.log_dir / "audit.log"),
                        "maxBytes"   : 52428800,
                        "backupCount": 30,
                        "encoding"   : "utf8",
                        "filters"    : ["smart_filter_for_files"],
                    },
                    "security_file": {
                        "class"      : "logging.handlers.RotatingFileHandler",
                        "level"      : "INFO",
                        "formatter"  : "json",
                        "filename"   : str(self.log_dir / "security.log"),
                        "maxBytes"   : 52428800,
                        "backupCount": 25,
                        "encoding"   : "utf8",
                    },
                },
                "loggers": {
                    "root"  : {"level": "WARNING", "handlers": ["console"]},
                    "vohrad": {
                        "level"    : self.log_level,
                        "handlers" : ["console", "file", "error_file"],
                        "propagate": False,
                    },
                    "vohrad.audit"   : {"level": "INFO", "handlers": ["audit_file"], "propagate": False},
                    "vohrad.security": {"level": "INFO", "handlers": ["security_file"], "propagate": False},
                    "uvicorn.error"  : {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
                    "uvicorn.access" : {"level": "WARNING", "handlers": ["file"], "propagate": False},
                },
            }
        )

        return config

    def _testing_config(self) -> Dict[str, Any]:
        """Testing environment configuration - minimal logging to avoid test noise."""
        config = self._base_config()

        config.update(
            {
                "handlers": {
                    "console": {
                        "class"    : "logging.StreamHandler",
                        "level"    : "ERROR",
                        "formatter": "simple",
                        "stream"   : "ext://sys.stdout",
                    }
                },
                "loggers": {
                    "root"  : {"level" : "ERROR", "handlers" : ["console"]},
                    "vohrad": {"level" : "WARNING", "handlers" : ["console"], "propagate": False},
                },
            }
        )

        return config

    def _apply_smart_filters(self):
        """Apply smart filters to reduce noise across all relevant loggers."""
        smart_filter = SmartFilter()
        root_logger  = logging.getLogger()

        for handler in root_logger.handlers:
            handler.addFilter(smart_filter)

        logger_names = [
            "vohrad",
            "uvicorn",
            "uvicorn.error",
        ]

        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)

            for handler in logger.handlers:
                handler.addFilter(smart_filter)
