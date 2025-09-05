"""JWT token models and payloads following RFC 7519."""

from config.jwt import get_jwt_config
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional
from uuid import UUID


class TokenSubject(BaseModel):
    """Token subject information."""
    user_id  : UUID
    email    : str
    tenant_id: Optional[UUID] = None
    user_type: str = Field(..., pattern="^(user|admin)$")


class AccessTokenPayload(BaseModel):
    """Access token payload following RFC 7519."""

    # RFC 7519 registered claims
    sub: str                    # Subject (user_id)
    iss: str                    # Issuer
    aud: str                    # Audience
    exp: int                    # Expiration time
    iat: int                    # Issued at
    nbf: int                    # Not before
    jti: str                    # JWT ID

    # Custom claims
    email     : str
    tenant_id : Optional[str] = None
    user_type : str = Field(..., pattern="^(user|admin)$")
    token_type: str = "access"

    @field_validator("sub")
    @classmethod
    def validate_subject(cls, v):
        """Ensure subject is valid UUID string."""
        try:
            UUID(v)
            return v
        except ValueError as e:
            raise ValueError("Subject must be valid UUID") from e

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, v):
        """Ensure tenant_id is valid UUID string if provided."""
        if v is not None:
            try:
                UUID(v)
                return v
            except ValueError as e:
                raise ValueError("Tenant ID must be valid UUID") from e
        return v


class RefreshTokenPayload(BaseModel):
    """Refresh token payload with minimal claims for security."""

    # RFC 7519 registered claims
    sub: str                    # Subject (user_id)
    iss: str                    # Issuer
    aud: str                    # Audience
    exp: int                    # Expiration time
    iat: int                    # Issued at
    nbf: int                    # Not before
    jti: str                    # JWT ID

    # Custom claims
    tenant_id : Optional[str] = None
    user_type : str           = Field(..., pattern="^(user|admin)$")
    token_type: str           = "refresh"

    @field_validator("sub")
    @classmethod
    def validate_subject(cls, v):
        """Ensure subject is valid UUID string."""
        try:
            UUID(v)
            return v
        except ValueError as e:
            raise ValueError("Subject must be valid UUID") from e


class AccessToken(BaseModel):
    """Access token with metadata."""
    token     : str
    payload   : AccessTokenPayload
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until expiration."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))


class RefreshToken(BaseModel):
    """Refresh token with metadata."""
    token     : str
    payload   : RefreshTokenPayload
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until expiration."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token : AccessToken
    refresh_token: RefreshToken
    token_type   : str = "Bearer"

    @property
    def expires_in(self) -> int:
        """Access token expiration in seconds."""
        return self.access_token.expires_in_seconds

    @property
    def refresh_expires_in(self) -> int:
        """Refresh token expiration in seconds."""
        return self.refresh_token.expires_in_seconds

    def to_response(self) -> dict[str, Any]:
        """Convert to API response format."""
        return {
            "access_token"      : self.access_token.token,
            "refresh_token"     : self.refresh_token.token,
            "token_type"        : self.token_type,
            "expires_in"        : self.expires_in,
            "refresh_expires_in": self.refresh_expires_in
        }


class AuthenticatedUser(BaseModel):
    """Authenticated user context from token."""
    user_id  : UUID
    email    : str
    tenant_id: Optional[UUID] = None
    user_type: str

    def is_admin(self) -> bool:
        """Check if user is global admin."""
        return self.user_type == "admin"

    def is_tenant_user(self) -> bool:
        """Check if user is tenant user."""
        return self.user_type == "user" and self.tenant_id is not None

    """Factory functions for creating token payloads"""


def create_user_access_payload(
    user_id  : UUID,
    email    : str,
    tenant_id: UUID,
    user_version: float | None = None
) -> dict[str, Any]:
    """Create access token payload for tenant user."""
    from uuid import uuid4
    jwt_config = get_jwt_config()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=jwt_config.access_token_expire_minutes)

    return {
        "sub"       : str(user_id),
        "iss"       : jwt_config.issuer,
        "aud"       : jwt_config.audience,
        "exp"       : int(expires.timestamp()),
        "iat"       : int(now.timestamp()),
        "nbf"       : int(now.timestamp()),
        "jti"       : str(uuid4()),
        "email"     : email,
        "tenant_id" : str(tenant_id),
        "user_type" : "user",
        "token_type": "access",
        "user_version": user_version
    }


def create_admin_access_payload(
    admin_id: UUID,
    email   : str,
    user_version: float | None = None
) -> dict[str, Any]:
    """Create access token payload for global admin."""
    from uuid import uuid4
    jwt_config = get_jwt_config()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=jwt_config.access_token_expire_minutes)

    return {
        "sub"       : str(admin_id),
        "iss"       : jwt_config.issuer,
        "aud"       : jwt_config.audience,
        "exp"       : int(expires.timestamp()),
        "iat"       : int(now.timestamp()),
        "nbf"       : int(now.timestamp()),
        "jti"       : str(uuid4()),
        "email"     : email,
        "tenant_id" : None,
        "user_type" : "admin",
        "token_type": "access",
        "user_version": user_version
    }


def create_refresh_payload(
    user_id  : UUID,
    tenant_id: Optional[UUID] = None,
    user_type: str = "user"
) -> dict[str, Any]:
    """Create refresh token payload."""
    from uuid import uuid4
    jwt_config = get_jwt_config()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=7)

    return {
        "sub"       : str(user_id),
        "iss"       : jwt_config.issuer,
        "aud"       : jwt_config.audience,
        "exp"       : int(expires.timestamp()),
        "iat"       : int(now.timestamp()),
        "nbf"       : int(now.timestamp()),
        "jti"       : str(uuid4()),
        "tenant_id" : str(tenant_id) if tenant_id else None,
        "user_type" : user_type,
        "token_type": "refresh"
    }
