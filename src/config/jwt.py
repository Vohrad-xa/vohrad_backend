"""JWT-specific configuration and settings following enterprise patterns."""

from config.settings import get_settings
from typing import Optional


class JWTConfig:
    """JWT configuration manager providing centralized settings access."""

    def __init__(self):
        self._app_settings = get_settings()

    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expiration in minutes."""
        return self._app_settings.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        """Get refresh token expiration in days."""
        return self._app_settings.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def algorithm(self) -> str:
        """Get JWT signing algorithm."""
        return self._app_settings.JWT_ALGORITHM

    @property
    def issuer(self) -> str:
        """Get JWT issuer."""
        return self._app_settings.JWT_ISSUER or self._app_settings.APP_NAME

    @property
    def audience(self) -> str:
        """Get JWT audience."""
        return self._app_settings.JWT_AUDIENCE or self._app_settings.APP_NAME

    @property
    def require_iat(self) -> bool:
        """Whether to require 'issued at' claim."""
        return self._app_settings.JWT_REQUIRE_IAT

    @property
    def require_nbf(self) -> bool:
        """Whether to require 'not before' claim."""
        return self._app_settings.JWT_REQUIRE_NBF

    @property
    def require_jti(self) -> bool:
        """Whether to require JWT ID claim."""
        return self._app_settings.JWT_REQUIRE_JTI

    @property
    def leeway(self) -> int:
        """Get token expiration leeway."""
        return self._app_settings.JWT_LEEWAY

    @property
    def verify_signature(self) -> bool:
        """Whether to verify JWT signature."""
        return self._app_settings.JWT_VERIFY_SIGNATURE

    @property
    def verify_expiration(self) -> bool:
        """Whether to verify token expiration."""
        return self._app_settings.JWT_VERIFY_EXPIRATION

    @property
    def verify_audience(self) -> bool:
        """Whether to verify audience claim."""
        return self._app_settings.JWT_VERIFY_AUDIENCE

    @property
    def verify_issuer(self) -> bool:
        """Whether to verify issuer claim."""
        return self._app_settings.JWT_VERIFY_ISSUER


# Singleton instance
_jwt_config: Optional[JWTConfig] = None


def get_jwt_config() -> JWTConfig:
    """Get JWT configuration singleton instance."""
    global _jwt_config
    if _jwt_config is None:
        _jwt_config = JWTConfig()
    return _jwt_config
