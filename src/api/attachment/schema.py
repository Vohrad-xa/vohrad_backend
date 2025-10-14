"""Attachment schemas."""

from api.common.schemas import BaseCreateSchema, BaseResponseSchema, BaseUpdateSchema
from constants.attachments import (
    MAX_UPLOAD_SIZE,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MIME_TYPES,
    AttachmentKind,
    AttachmentTarget,
    detect_attachment_kind,
)
from datetime import datetime
from fastapi import File, Form, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator
from typing import Optional
from uuid import UUID


class AttachmentBase(BaseModel):
    """Shared fields for attachment metadata."""

    description: Optional[str] = Field(default=None, max_length=5000)
    category   : Optional[str] = Field(default=None, max_length=100)


class AttachmentCreate(AttachmentBase, BaseCreateSchema):
    """Schema used when creating a new attachment."""

    target_type      : AttachmentTarget = Field(alias="attachable_type")
    target_id        : UUID             = Field(alias="attachable_id")
    original_filename: Optional[str]    = Field(default=None, max_length=255)
    filename         : Optional[str]    = Field(default=None, max_length=255)
    file_type        : Optional[str]    = Field(default=None, max_length=100)
    extension        : Optional[str]    = Field(default=None, max_length=10)
    size             : Optional[int]    = Field(default=None, ge=0, le=MAX_UPLOAD_SIZE)
    user_id          : Optional[UUID]   = None

    @field_validator("extension")
    @classmethod
    def validate_extension(cls, value: Optional[str]) -> Optional[str]:
        if value and value.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file extension")
        return value

    @field_validator("file_type")
    @classmethod
    def validate_mime_type(cls, value: Optional[str]) -> Optional[str]:
        if value and value not in SUPPORTED_MIME_TYPES:
            raise ValueError("Unsupported MIME type")
        return value

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value > MAX_UPLOAD_SIZE:
            raise ValueError("File size exceeds maximum upload limit")
        return value


class AttachmentUpdate(AttachmentBase, BaseUpdateSchema):
    """Schema used when updating attachment metadata."""

    user_id: Optional[UUID] = None


class AttachmentResponse(AttachmentBase, BaseResponseSchema):
    """Serialized attachment metadata."""

    id               : UUID
    filename         : str
    original_filename: str
    file_type        : str
    extension        : Optional[str]
    size             : int
    file_path        : str
    user_id          : Optional[UUID]
    deleted_at       : Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @computed_field  # type: ignore[misc]
    @property
    def kind(self) -> AttachmentKind:
        return detect_attachment_kind(self.file_type, self.extension)


class AttachmentLinkRequest(BaseModel):
    """Link an existing attachment to a new entity."""

    target_type: AttachmentTarget
    target_id: UUID


class AttachmentUploadForm(BaseModel):
    """Form helper for multipart attachment uploads."""

    file             : UploadFile
    attachable_type  : AttachmentTarget
    attachable_id    : UUID
    description      : Optional[str] = None
    category         : Optional[str] = None
    filename         : Optional[str] = None
    original_filename: Optional[str] = None
    file_type        : Optional[str] = None
    extension        : Optional[str] = None
    size             : Optional[int] = Field(default=None, ge=0, le=MAX_UPLOAD_SIZE)
    user_id          : Optional[UUID] = None

    @classmethod
    def as_form(
        cls,
        file: UploadFile = File(...),
        attachable_type: AttachmentTarget = Form(..., alias="attachable_type"),
        attachable_id: UUID = Form(..., alias="attachable_id"),
        description: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        filename: Optional[str] = Form(None),
        original_filename: Optional[str] = Form(None),
        file_type: Optional[str] = Form(None),
        extension: Optional[str] = Form(None),
        size: Optional[int] = Form(None),
        user_id: Optional[UUID] = Form(None),
    ) -> "AttachmentUploadForm":
        return cls(
            file              = file,
            attachable_type   = attachable_type,
            attachable_id     = attachable_id,
            description       = description,
            category          = category,
            filename          = filename,
            original_filename = original_filename,
            file_type         = file_type,
            extension         = extension,
            size              = size,
            user_id           = user_id,
        )


class AttachmentFilterParams(BaseModel):
    """Filter options accepted by attachment listings."""

    category       : Optional[str]          = None
    file_type      : Optional[str]          = None
    user_id        : Optional[UUID]         = None
    min_size       : Optional[int]          = Field(default=None, ge=0)
    max_size       : Optional[int]          = Field(default=None, ge=0)
    include_deleted: bool                   = False
    target_type    : Optional[AttachmentTarget] = None
    target_id      : Optional[UUID]         = None
    kind           : Optional[AttachmentKind] = None

    @model_validator(mode="after")
    def validate_size_bounds(self) -> "AttachmentFilterParams":
        if self.max_size is not None:
            if self.max_size > MAX_UPLOAD_SIZE:
                raise ValueError("max_size exceeds maximum upload limit")
            if self.min_size is not None and self.max_size < self.min_size:
                raise ValueError("max_size must be greater than or equal to min_size")
        return self

    @classmethod
    def as_query(
        cls,
        category: Optional[str] = Query(None),
        file_type: Optional[str] = Query(None),
        user_id: Optional[UUID] = Query(None),
        min_size: Optional[int] = Query(None, ge=0),
        max_size: Optional[int] = Query(None, ge=0),
        include_deleted: bool = Query(False),
        target_type: Optional[AttachmentTarget] = Query(None),
        target_id: Optional[UUID] = Query(None),
        kind: Optional[AttachmentKind] = Query(None),
    ) -> "AttachmentFilterParams":
        data = {
            "category": category,
            "file_type": file_type,
            "user_id": user_id,
            "min_size": min_size,
            "max_size": max_size,
            "include_deleted": include_deleted,
            "target_type": target_type,
            "target_id": target_id,
            "kind": kind,
        }
        return cls.model_validate(data)
