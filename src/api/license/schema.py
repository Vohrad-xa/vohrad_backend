"""License schemas."""

from api.common.schemas import BaseResponseSchema
from constants import LicenseStatus
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID


class LicenseCreate(BaseModel):
    """Schema for creating license."""

    tenant_id: UUID
    name     : str = Field(..., min_length=1, max_length=256)
    price    : Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, max_digits=10)
    seats    : int = Field(default=1, ge=1)
    starts_at: datetime
    ends_at  : Optional[datetime] = None
    status   : str = LicenseStatus.INACTIVE.value
    features : Optional[dict] = None
    meta     : Optional[dict] = None

    @field_validator("seats")
    @classmethod
    def validate_seats(cls, v):
        if v < 1:
            raise ValueError("Seats must be at least 1")
        return v

    @field_validator("ends_at")
    @classmethod
    def validate_ends_at(cls, v, info):
        if v and info.data.get("starts_at") and v <= info.data["starts_at"]:
            raise ValueError("End date must be after start date")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = [status.value for status in LicenseStatus]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class LicenseUpdate(BaseModel):
    """Schema for updating license - all fields optional."""

    name     : Optional[str]      = Field(None, min_length=1, max_length=256)
    price    : Optional[Decimal]  = Field(None, ge=0, decimal_places=2, max_digits=10)
    seats    : Optional[int]      = Field(None, ge=1)
    starts_at: Optional[datetime] = None
    ends_at  : Optional[datetime] = None
    status   : Optional[str]      = None
    features : Optional[dict]     = None
    meta     : Optional[dict]     = None

    @field_validator("seats")
    @classmethod
    def validate_seats(cls, v):
        if v is not None and v < 1:
            raise ValueError("Seats must be at least 1")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = [status.value for status in LicenseStatus]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class LicenseResponse(BaseResponseSchema):
    """Schema for license response."""

    id         : UUID
    tenant_id  : UUID
    name       : str
    price      : Decimal
    seats      : int
    license_key: str
    starts_at  : datetime
    ends_at    : Optional[datetime]
    status     : str
    features   : Optional[dict]
    meta       : Optional[dict]
    created_at : datetime
    updated_at : datetime
