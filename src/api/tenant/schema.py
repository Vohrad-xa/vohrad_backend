from api.common import BaseResponseSchema
from constants import TenantDefaults
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import field_validator
from typing import Optional
from uuid import UUID

class TenantBase(BaseModel):
    """Base tenant schema"""

    sub_domain: Optional[str] = None
    tenant_schema_name: Optional[str] = None
    status: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    remarks: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    industry: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None

class TenantCreate(TenantBase):
    """Schema for creating tenant"""

    sub_domain: str
    status: str = TenantDefaults.DEFAULT_STATUS
    email: EmailStr

    @field_validator("sub_domain")
    @classmethod

    def validate_sub_domain(cls, v):
        if not v or not v.strip():
            raise ValueError("sub_domain cannot be empty")
        return v

class TenantUpdate(TenantBase):
    """Schema for updating tenant"""

    pass

class TenantResponse(BaseResponseSchema):
    """Schema for tenant response"""

    tenant_id: UUID
    sub_domain: str
    tenant_schema_name: str
    status: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    street: Optional[str] = None
    street_number: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    remarks: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    industry: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
