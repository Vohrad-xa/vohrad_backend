import os
from observability.logger import get_logger
from observability.logger import setup_logging
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from typing import ClassVar
from typing import Optional

setup_logging()
logger = get_logger()

def get_settings():
    settings = Settings.instance()

    if settings.ENVIRONMENT == "development":
        return settings
    elif settings.ENVIRONMENT == "production":
        return settings
    else:
        raise ValueError("ENVIRONMENT variable is not set to development or production", settings.ENVIRONMENT)

class Settings(BaseSettings):
    """Application settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    BASE_DIR: str = Field(default_factory=lambda: os.path.dirname(os.path.abspath(__file__)))
    APP_NAME: str = Field(default="Multi-Tenant FastAPI Application", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Server settings
    HOST: str = Field(default="localhost", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # Database settings
    DB_USER: str = Field(description="Database username")
    DB_NAME: str = Field(description="Database name")
    DB_PASS: str = Field(description="Database password")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: str = Field(default="5432", description="Database port")

    # Security settings
    SECRET_KEY: Optional[str] = Field(default=None, description="Secret key for JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration time")

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default pagination page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination page size")

    @field_validator("ENVIRONMENT")
    @classmethod

    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod

    def validate_debug(cls, v):
        """Convert string debug values to boolean."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "on", "yes")
        return v

    @property

    def database_url(self) -> str:
        """Generate database URL from components."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"

    _instance: ClassVar[Optional["Settings"]] = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new Settings instance")
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    @classmethod

    def instance(cls) -> "Settings":
        """Get singleton instance of settings."""
        if cls._instance is None:
            cls._instance = cls()
            logger.info(f"Settings loaded for environment: {cls._instance.ENVIRONMENT}")
        return cls._instance
