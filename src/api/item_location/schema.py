"""ItemLocation schemas."""

from api.common.schemas import BaseResponseSchema
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID


class Item(BaseResponseSchema):
    """Compact item details for item-location responses."""

    id  : UUID
    name: str
    code: str


class Location(BaseResponseSchema):
    """Compact location details for item-location responses."""

    id  : UUID
    name: str
    code: str


class ItemLocationBase(BaseModel):
    """Base item location schema."""

    item_id    : UUID
    location_id: UUID
    quantity   : Decimal = Field(ge=1, decimal_places=2, max_digits=10)
    moved_date : Optional[date] = None
    notes      : Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v is None:
            raise ValueError("Quantity is required")
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        if v > 10000000:
            raise ValueError("Quantity cannot exceed 10,000,000")
        return v


class ItemLocationCreate(ItemLocationBase):
    """Schema for creating item location."""

    pass


class ItemLocationUpdate(BaseModel):
    """Schema for updating item location."""

    quantity  : Optional[Decimal] = Field(None, ge=1, decimal_places=2, max_digits=10)
    moved_date: Optional[date] = None
    notes     : Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v is not None:
            if v < 1:
                raise ValueError("Quantity must be at least 1")
            if v > 10000000:
                raise ValueError("Quantity cannot exceed 10,000,000")
        return v


class ItemLocationResponse(BaseResponseSchema):
    """Schema for item location response."""

    id        : UUID
    quantity  : Decimal
    moved_date: Optional[date] = None
    notes     : Optional[str] = None
    item      : Optional[Item] = None
    location  : Optional[Location] = None
