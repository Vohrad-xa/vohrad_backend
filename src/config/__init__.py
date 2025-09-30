"""Application configuration."""

from .keys import get_key_manager
from .settings import get_settings

__all__ = ["get_key_manager", "get_settings"]
