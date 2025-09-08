"""JWT-specific configuration and settings following enterprise patterns."""

from config.settings import get_settings
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class JWTSettings(BaseSettings):
    """JWT-specific configuration settings."""

    # Token expiration settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS  : int = Field(default=7, description="Refresh token expiration in days")

    # JWT algorithm settings
    JWT_ALGORITHM: str           = Field(default="RS256", description="JWT signing algorithm")
    JWT_ISSUER   : Optional[str] = Field(default=None, description="JWT issuer claim")
    JWT_AUDIENCE : Optional[str] = Field(default=None, description="JWT audience claim")

    # Security settings
    JWT_REQUIRE_IAT: bool = Field(default=True, description="Require 'issued at' claim")
    JWT_REQUIRE_NBF: bool = Field(default=True, description="Require 'not before' claim")
    JWT_REQUIRE_JTI: bool = Field(default=True, description="Require JWT ID claim")
    JWT_LEEWAY     : int  = Field(default=0, description="Leeway for token expiration in seconds")

    # Enhanced security settings
    JWT_VERIFY_SIGNATURE : bool = Field(default=True, description="Verify JWT signature")
    JWT_VERIFY_EXPIRATION: bool = Field(default=True, description="Verify token expiration")
    JWT_VERIFY_AUDIENCE  : bool = Field(default=True, description="Verify audience claim")
    JWT_VERIFY_ISSUER    : bool = Field(default=True, description="Verify issuer claim")

    # Token refresh settings
    REFRESH_TOKEN_ROTATE      : bool = Field(default=True, description="Rotate refresh tokens on use")
    MAX_REFRESH_TOKEN_AGE_DAYS: int  = Field(default=30, description="Maximum refresh token age in days")

    # Rate limiting for auth endpoints
    AUTH_RATE_LIMIT_ENABLED       : bool = Field(default=True, description="Enable rate limiting for auth endpoints")
    AUTH_RATE_LIMIT_REQUESTS      : int  = Field(default=5, description="Max auth requests per window")
    AUTH_RATE_LIMIT_WINDOW_MINUTES: int  = Field(default=15, description="Rate limit window in minutes")

    class Config:
        """JWT-specific configuration settings."""

        env_prefix     = "JWT_"
        case_sensitive = True


class JWTConfig:
    """JWT configuration manager providing centralized settings access."""

    def __init__(self):
        self._settings     = None
        self._app_settings = get_settings()

    @property
    def settings(self) -> JWTSettings:
        """Get JWT settings instance."""
        if self._settings is None:
            self._settings = JWTSettings()
        return self._settings

    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expiration in minutes."""
        return getattr(self._app_settings, "ACCESS_TOKEN_EXPIRE_MINUTES", None) or self.settings.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        """Get refresh token expiration in days."""
        return self.settings.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def algorithm(self) -> str:
        """Get JWT signing algorithm."""
        return self.settings.JWT_ALGORITHM

    @property
    def issuer(self) -> str:
        """Get JWT issuer."""
        return self.settings.JWT_ISSUER or self._app_settings.APP_NAME

    @property
    def audience(self) -> str:
        """Get JWT audience."""
        return self.settings.JWT_AUDIENCE or self._app_settings.APP_NAME

    @property
    def require_iat(self) -> bool:
        """Whether to require 'issued at' claim."""
        return self.settings.JWT_REQUIRE_IAT

    @property
    def require_nbf(self) -> bool:
        """Whether to require 'not before' claim."""
        return self.settings.JWT_REQUIRE_NBF

    @property
    def require_jti(self) -> bool:
        """Whether to require JWT ID claim."""
        return self.settings.JWT_REQUIRE_JTI

    @property
    def leeway(self) -> int:
        """Get token expiration leeway."""
        return self.settings.JWT_LEEWAY


# Singleton instance
_jwt_config: Optional[JWTConfig] = None


def get_jwt_config() -> JWTConfig:
    """Get JWT configuration singleton instance."""
    global _jwt_config
    if _jwt_config is None:
        _jwt_config = JWTConfig()
    return _jwt_config
