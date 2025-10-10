"""Admin API response schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class AdminResponse(BaseModel):
    """Admin user response."""

    id               : UUID
    email            : EmailStr
    first_name       : Optional[str] = None
    last_name        : Optional[str] = None
    role             : str
    is_active        : bool
    email_verified_at: Optional[datetime] = None
    city             : Optional[str] = None
    phone_number     : Optional[str] = None
    created_at       : datetime
    updated_at       : datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True
