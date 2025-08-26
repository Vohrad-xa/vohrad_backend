import os
import secrets
from typing import ClassVar, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from observability.logger import get_logger

def get_settings():
    settings = Settings.instance()

    if settings.ENVIRONMENT == "development":
        return settings
    elif settings.ENVIRONMENT == "production":
        return settings
    else:
        raise ValueError("ENVIRONMENT variable is not set to development or production", settings.ENVIRONMENT)

class Settings(BaseSettings):
    """Settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    """
    Application settings
    """
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    BASE_DIR: str = Field(default_factory=lambda: os.path.dirname(os.path.abspath(__file__)))
    APP_NAME: str = Field(default="Multi-Tenant FastAPI Application", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    """
    Server settings
    """
    HOST: str = Field(default="localhost", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    """
    Database settings
    """
    DB_USER: str = Field(description="Database username")
    DB_NAME: str = Field(description="Database name")
    DB_PASS: str = Field(description="Database password")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: str = Field(default="5432", description="Database port")

    """
    Security settings
    """
    SECRET_KEY: Optional[str] = Field(default=None, description="Secret key for JWT tokens and encryption")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration time")

    """
    Encryption settings
    """
    ENCRYPTION_KEY: Optional[str] = Field(default=None, description="Key for sensitive data encryption")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")

    """
    Pagination settings
    """
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default pagination page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination page size")

    """
    Logging settings
    """
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE_PATH: str = Field(default="logs/app.log", description="Main log file path")
    LOG_ERROR_FILE_PATH: str = Field(default="logs/error.log", description="Error log file path")
    LOG_MAX_BYTES: int = Field(default=10485760, description="Maximum log file size in bytes")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files to keep")

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

    @field_validator("LOG_LEVEL")
    @classmethod

    def validate_log_level(cls, v):
        """Validate log level value."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @field_validator("JWT_ALGORITHM")
    @classmethod

    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm is secure."""
        allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"JWT_ALGORITHM must be one of {allowed_algorithms}")
        return v

    @model_validator(mode="after")

    def validate_security_keys(self):
        """Validate security keys based on environment."""
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY:
                raise ValueError("SECRET_KEY is required for production environment")

            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters for production")

            if self.SECRET_KEY.isalnum() and len(self.SECRET_KEY) < 64:
                pass

        elif self.ENVIRONMENT == "development" and not self.SECRET_KEY:
            self.SECRET_KEY = self._generate_secure_key()

        return self

    def _generate_secure_key(self) -> str:
        """Generate a secure random key for development."""
        return secrets.token_urlsafe(64)

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
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    @classmethod

    def instance(cls) -> "Settings":
        """Get singleton instance of settings."""
        if cls._instance is None:
            cls._instance = cls()
            try:
                logger = get_logger("vohrad.settings")
                assert cls._instance is not None
                logger.info(f"Settings loaded for environment: {cls._instance.ENVIRONMENT}")
            except Exception:
                pass
        assert cls._instance is not None
        return cls._instance
