"""Attachment-related constants."""

from enum import StrEnum

MAX_UPLOAD_SIZE               = 10 * 1024 * 1024  # 10MB in bytes
SUPPORTED_IMAGE_EXTENSIONS    = ["jpg", "jpeg", "png", "gif", "webp"]
SUPPORTED_DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "txt", "csv"]
SUPPORTED_EXTENSIONS          = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_DOCUMENT_EXTENSIONS

# Supported MIME types
SUPPORTED_IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
]

SUPPORTED_DOCUMENT_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
]

SUPPORTED_MIME_TYPES = SUPPORTED_IMAGE_MIME_TYPES + SUPPORTED_DOCUMENT_MIME_TYPES

# File type categories
CATEGORY_IMAGE    = "image"
CATEGORY_DOCUMENT = "document"
CATEGORY_MANUAL   = "manual"
CATEGORY_WARRANTY = "warranty"
CATEGORY_INVOICE  = "invoice"
CATEGORY_OTHER    = "other"

# Attachable entity types
ATTACHABLE_TYPE_ITEM = "item"
ATTACHABLE_TYPE_LOCATION = "location"
ATTACHABLE_TYPE_ITEM_LOCATION = "item_location"


class AttachmentTarget(StrEnum):
    ITEM = "item"
    LOCATION = "location"
    ITEM_LOCATION = "item_location"


SUPPORTED_ATTACHABLE_TYPES = [target.value for target in AttachmentTarget]
