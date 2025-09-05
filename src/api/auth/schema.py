"""Authentication request and response schemas following enterprise patterns."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class UserLoginRequest(BaseModel):
    """User login request schema with automatic tenant resolution."""
    email    : EmailStr
    password : str = Field(..., min_length=1, description="User password")
    tenant_id: Optional[UUID] = Field(
        None,
        description = "Optional tenant UUID - auto-resolved from subdomain if not provided"
    )


class AdminLoginRequest(BaseModel):
    """Global admin login request schema."""
    email   : EmailStr
    password: str = Field(..., min_length=1, description="Admin password")


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(..., min_length=1, description="Valid refresh token")


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token      : str = Field(..., description="JWT access token")
    refresh_token     : str = Field(..., description="JWT refresh token")
    token_type        : str = Field(default="Bearer", description="Token type")
    expires_in        : int = Field(..., description="Access token expiration in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration in seconds")


class AuthStatusResponse(BaseModel):
    """Authentication service status response schema."""
    service    : str = Field(default="authentication", description="Service name")
    status     : str = Field(default="healthy", description="Service health status")
    jwt_service: str = Field(default="operational", description="JWT service status")


class SecurityStatusResponse(BaseModel):
    """Security configuration status response schema."""
    service                  : str       = Field(default="security", description="Service name")
    secret_key_configured    : bool      = Field(..., description="Whether SECRET_KEY is configured")
    secret_key_length        : int       = Field(..., description="Length of SECRET_KEY")
    secret_key_strength      : str       = Field(..., description="Strength assessment of SECRET_KEY")
    encryption_key_configured: bool      = Field(..., description="Whether ENCRYPTION_KEY is configured")
    jwt_algorithm            : str       = Field(..., description="JWT signing algorithm in use")
    environment              : str       = Field(..., description="Current environment")
    warnings                 : list[str] = Field(..., description="Security warnings")
