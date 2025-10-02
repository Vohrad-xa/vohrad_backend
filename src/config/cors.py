"""Centralised CORS configuration utilities."""

from dataclasses import dataclass
from typing import Iterable, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_settings


@dataclass(frozen=True)
class CORSConfig:
    """Immutable CORS configuration container."""

    allow_origins    : Sequence[str]
    allow_credentials: bool = True
    allow_methods    : Sequence[str] = ("*",)
    allow_headers    : Sequence[str] = ("*",)


def _dedupe(sequence: Iterable[str]) -> list[str]:
    """Preserve order while removing duplicates."""

    seen: set[str] = set()
    result: list[str] = []
    for item in sequence:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def get_cors_config() -> CORSConfig:
    """Build CORS configuration from application settings."""

    settings = get_settings()
    origins  = getattr(settings, 'CORS_ALLOWED_ORIGINS', None) or settings.CORS_ALLOW_ORIGINS or []
    return CORSConfig(allow_origins=origins)


def install_cors(app: FastAPI) -> None:
    """Install the CORS middleware using centralised configuration."""

    config = get_cors_config()
    if not config.allow_origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins     = _dedupe(config.allow_origins),
        allow_credentials = config.allow_credentials,
        allow_methods     = list(config.allow_methods),
        allow_headers     = list(config.allow_headers),
    )
