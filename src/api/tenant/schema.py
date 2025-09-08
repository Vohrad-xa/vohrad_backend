"""Tenant schemas."""


from api.common.schemas import BaseResponseSchema
from constants import TenantDefaults, ValidationMessages
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional
from uuid import UUID


class TenantCreate(BaseModel):
    """Schema for creating tenant - only required fields"""

    sub_domain        : str
    tenant_schema_name: str
    email             : EmailStr
    status            : str = TenantDefaults.DEFAULT_STATUS
    telephone         : Optional[str] = None
    street            : Optional[str] = None
    street_number     : Optional[str] = None
    city              : Optional[str] = None
    province          : Optional[str] = None
    postal_code       : Optional[str] = None
    remarks           : Optional[str] = None
    website           : Optional[str] = None
    logo              : Optional[str] = None
    industry          : Optional[str] = None
    tax_id            : Optional[str] = None
    billing_address   : Optional[str] = None
    country           : Optional[str] = None
    timezone          : Optional[str] = None

    @field_validator("sub_domain")
    @classmethod
    def validate_sub_domain(cls, v):
        if not v or not v.strip():
            raise ValueError(ValidationMessages.SUBDOMAIN_REQUIRED)
        return v.strip().lower()

    @field_validator("tenant_schema_name")
    @classmethod
    def validate_tenant_schema_name(cls, v):
        if not v or not v.strip():
            raise ValueError(ValidationMessages.TENANT_SCHEMA_REQUIRED)
        return v.strip().lower()


class TenantUpdate(BaseModel):
    """Schema for updating tenant - all fields optional except critical ones"""

    email          : Optional[EmailStr] = None
    status         : Optional[str]      = None
    telephone      : Optional[str]      = None
    street         : Optional[str]      = None
    street_number  : Optional[str]      = None
    city           : Optional[str]      = None
    province       : Optional[str]      = None
    postal_code    : Optional[str]      = None
    remarks        : Optional[str]      = None
    website        : Optional[str]      = None
    logo           : Optional[str]      = None
    industry       : Optional[str]      = None
    tax_id         : Optional[str]      = None
    billing_address: Optional[str]      = None
    country        : Optional[str]      = None
    timezone            : Optional[str] = None
    business_hour_start : Optional[int] = None
    business_hour_end   : Optional[int] = None

    @field_validator("business_hour_start")
    @classmethod
    def validate_start(cls, v):
        if v is None:
            return v
        if not (0 <= int(v) <= 23):
            raise ValueError("business_hour_start must be between 0 and 23")
        return int(v)

    @field_validator("business_hour_end")
    @classmethod
    def validate_end(cls, v):
        if v is None:
            return v
        if not (0 <= int(v) <= 23):
            raise ValueError("business_hour_end must be between 0 and 23")
        return int(v)

    @model_validator(mode="after")
    def validate_hours_order(self):
        if self.business_hour_start is not None and self.business_hour_end is not None:
            if self.business_hour_start > self.business_hour_end:
                raise ValueError("business_hour_start must be <= business_hour_end")
        return self


class TenantResponse(BaseResponseSchema):
    """Schema for tenant response"""

    tenant_id         : UUID
    sub_domain        : str
    tenant_schema_name: str
    status            : str
    email             : Optional[EmailStr] = None
    telephone         : Optional[str] = None
    street            : Optional[str] = None
    street_number     : Optional[str] = None
    city              : Optional[str] = None
    province          : Optional[str] = None
    postal_code       : Optional[str] = None
    remarks           : Optional[str] = None
    website           : Optional[str] = None
    logo              : Optional[str] = None
    industry          : Optional[str] = None
    tax_id            : Optional[str] = None
    billing_address   : Optional[str] = None
    country           : Optional[str] = None
    timezone            : Optional[str] = None
    business_hour_start : Optional[int] = None
    business_hour_end   : Optional[int] = None


class TenantSettingsUpdate(BaseModel):
    """Limited schema for tenant-managed settings (timezone and working hours)."""

    timezone           : Optional[str] = None
    business_hour_start: Optional[int] = None
    business_hour_end  : Optional[int] = None

    @field_validator("business_hour_start")
    @classmethod
    def validate_start(cls, v):
        if v is None:
            return v
        if not (0 <= int(v) <= 23):
            raise ValueError("business_hour_start must be between 0 and 23")
        return int(v)

    @field_validator("business_hour_end")
    @classmethod
    def validate_end(cls, v):
        if v is None:
            return v
        if not (0 <= int(v) <= 23):
            raise ValueError("business_hour_end must be between 0 and 23")
        return int(v)

    @field_validator("timezone")
    @classmethod
    def normalize_tz(cls, v):
        return v.strip() if v else v

    @model_validator(mode="after")
    def validate_hours_order(self):
        if self.business_hour_start is not None and self.business_hour_end is not None:
            if self.business_hour_start > self.business_hour_end:
                raise ValueError("business_hour_start must be <= business_hour_end")
        return self
