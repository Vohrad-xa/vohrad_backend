"""Item schemas."""

from api.common.schemas import BaseResponseSchema
from api.common.validators import CommonValidators
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Any, Literal, Optional
from uuid import UUID


class ItemBase(BaseModel):
    """Base item schema."""

    name                  : str
    code                  : str
    barcode               : Optional[str] = None
    description           : Optional[str] = None
    tracking_mode         : Literal["abstract", "standard", "serialized"] = "abstract"
    price                 : Optional[Decimal] = Field(None, ge=0, decimal_places=2, max_digits=10)
    serial_number         : Optional[str] = None
    notes                 : Optional[str] = None
    is_active             : bool = True
    specifications        : Optional[dict[str, Any]] = None
    tracking_change_reason: Optional[str] = None
    user_id               : Optional[UUID] = None
    parent_item_id        : Optional[UUID] = None
    item_relation_id      : Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v and len(v) > 100:
            raise ValueError("Name must not exceed 100 characters")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v and len(v) > 50:
            raise ValueError("Code must not exceed 50 characters")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price must be non-negative")
        return v

    @field_validator("specifications")
    @classmethod
    def validate_specifications(cls, v):
        return CommonValidators.validate_jsonb_specifications(v)


class ItemCreate(ItemBase):
    """Schema for creating item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating item."""

    name                  : Optional[str] = None
    code                  : Optional[str] = None
    barcode               : Optional[str] = None
    description           : Optional[str] = None
    tracking_mode         : Optional[Literal["abstract", "standard", "serialized"]] = None
    price                 : Optional[Decimal] = Field(None, ge=0, decimal_places=2, max_digits=10)
    serial_number         : Optional[str] = None
    notes                 : Optional[str] = None
    is_active             : Optional[bool] = None
    specifications        : Optional[dict[str, Any]] = None
    tracking_change_reason: Optional[str] = None
    user_id               : Optional[UUID] = None
    parent_item_id        : Optional[UUID] = None
    item_relation_id      : Optional[UUID] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v and len(v) > 100:
            raise ValueError("Name must not exceed 100 characters")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v and len(v) > 50:
            raise ValueError("Code must not exceed 50 characters")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price must be non-negative")
        return v


class ItemLocationData(BaseModel):
    """Location summary for item responses (includes quantity)."""

    id      : UUID
    name    : str
    code    : str
    quantity: Decimal


class ItemResponse(BaseResponseSchema):
    """Schema for item response (list and create views)."""

    id                    : UUID
    name                  : str
    code                  : str
    barcode               : Optional[str] = None
    description           : Optional[str] = None
    tracking_mode         : str
    price                 : Optional[Decimal] = None
    serial_number         : Optional[str] = None
    notes                 : Optional[str] = None
    is_active             : bool
    specifications        : Optional[dict[str, Any]] = None
    tracking_changed_at   : Optional[datetime] = None
    tracking_change_reason: Optional[str] = None
    user_id               : Optional[UUID] = None
    parent_item_id        : Optional[UUID] = None
    item_relation_id      : Optional[UUID] = None


class ItemDetailResponse(ItemResponse):
    """Detailed item response with locations (detail views only)."""

    item_locations: Optional[list[Any]] = Field(default=None, exclude=True)

    @computed_field  # type: ignore[misc]
    @property
    def locations(self) -> Optional[list[ItemLocationData]]:
        """Derived locations with quantities from item_locations relationship when loaded."""
        if not self.item_locations:
            return None

        return [
            ItemLocationData(
                id=il.location.id,
                name=il.location.name,
                code=il.location.code,
                quantity=il.quantity,
            )
            for il in self.item_locations
            if il.location
        ] or None
