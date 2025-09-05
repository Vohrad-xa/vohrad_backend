from api.common.schemas import BaseResponseSchema
from constants import TenantDefaults, ValidationMessages
from pydantic import BaseModel, EmailStr, field_validator
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

    email           : Optional[EmailStr] = None
    status          : Optional[str] = None
    telephone       : Optional[str] = None
    street          : Optional[str] = None
    street_number   : Optional[str] = None
    city            : Optional[str] = None
    province        : Optional[str] = None
    postal_code     : Optional[str] = None
    remarks         : Optional[str] = None
    website         : Optional[str] = None
    logo            : Optional[str] = None
    industry        : Optional[str] = None
    tax_id          : Optional[str] = None
    billing_address : Optional[str] = None
    country         : Optional[str] = None
    timezone        : Optional[str] = None


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
    timezone          : Optional[str] = None
