"""Authentication request and response schemas following enterprise patterns."""

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
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
