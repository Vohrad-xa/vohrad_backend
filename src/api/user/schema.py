from api.common import BaseResponseSchema
from api.common import CommonValidators
from datetime import date
from datetime import datetime
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import field_validator
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema"""

    first_name   : Optional[str] = None
    last_name    : Optional[str] = None
    tenant_role  : Optional[str] = None
    email        : EmailStr
    date_of_birth: Optional[date] = None
    address      : Optional[str] = None
    city         : Optional[str] = None
    province     : Optional[str] = None
    postal_code  : Optional[str] = None
    country      : Optional[str] = None
    phone_number : Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v):
        return CommonValidators.validate_name_field(v, "First name")

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v):
        return CommonValidators.validate_name_field(v, "Last name")

    @field_validator("tenant_role")
    @classmethod
    def validate_tenant_role_length(cls, v):
        return CommonValidators.validate_role_field(v, 32)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_length(cls, v):
        return CommonValidators.validate_phone_number(v)


class UserCreate(UserBase):
    """Schema for creating user"""

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        return CommonValidators.validate_password_strength(v)


class UserUpdate(BaseModel):
    """Schema for updating user"""

    first_name    : Optional[str]      = None
    last_name     : Optional[str]      = None
    tenant_role   : Optional[str]      = None
    email         : Optional[EmailStr] = None
    date_of_birth : Optional[date]     = None
    address       : Optional[str]      = None
    city          : Optional[str]      = None
    province      : Optional[str]      = None
    postal_code   : Optional[str]      = None
    country       : Optional[str]      = None
    phone_number  : Optional[str]      = None

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v):
        return CommonValidators.validate_name_field(v, "First name")

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, v):
        return CommonValidators.validate_name_field(v, "Last name")

    @field_validator("tenant_role")
    @classmethod
    def validate_tenant_role_length(cls, v):
        return CommonValidators.validate_role_field(v, 32)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_length(cls, v):
        return CommonValidators.validate_phone_number(v)


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""

    current_password: str
    new_password    : str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        return CommonValidators.validate_password_strength(v)

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v, info):
        if "new_password" in info.data:
            return CommonValidators.validate_password_confirmation(v, info.data["new_password"])
        return v


class UserResponse(BaseResponseSchema):
    """Schema for user response"""

    id               : UUID
    tenant_id        : UUID
    first_name       : Optional[str] = None
    last_name        : Optional[str] = None
    tenant_role      : Optional[str] = None
    email            : str
    email_verified_at: Optional[datetime] = None
    date_of_birth    : Optional[date]     = None
    address          : Optional[str]      = None
    city             : Optional[str]      = None
    province         : Optional[str]      = None
    postal_code      : Optional[str]      = None
    country          : Optional[str]      = None
    phone_number     : Optional[str]      = None
