"""Basic application settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Basic application settings."""
    
    app_name: str = "Vohrad API"
    version: str = "1.0.0"
    environment: str = "development"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()