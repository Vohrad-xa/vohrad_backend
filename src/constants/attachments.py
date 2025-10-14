"""Attachment-related constants."""

from enum import StrEnum

MAX_UPLOAD_SIZE               = 10 * 1024 * 1024  # 10MB in bytes
SUPPORTED_IMAGE_EXTENSIONS    = ["jpg", "jpeg", "png", "gif", "webp"]
SUPPORTED_DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "txt", "csv"]
SUPPORTED_VIDEO_EXTENSIONS    = ["mp4", "mov", "avi", "wmv", "mkv", "flv", "mpeg"]
SUPPORTED_ARCHIVE_EXTENSIONS  = ["zip", "rar", "7z", "tar", "gz", "tgz", "bz2"]
SUPPORTED_EXTENSIONS          = (
    SUPPORTED_IMAGE_EXTENSIONS
    + SUPPORTED_DOCUMENT_EXTENSIONS
    + SUPPORTED_VIDEO_EXTENSIONS
    + SUPPORTED_ARCHIVE_EXTENSIONS
)

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

SUPPORTED_VIDEO_MIME_TYPES = [
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/x-matroska",
]

SUPPORTED_ARCHIVE_MIME_TYPES = [
    "application/zip",
    "application/x-7z-compressed",
    "application/x-tar",
    "application/x-gtar",
    "application/gzip",
    "application/x-rar-compressed",
]

SUPPORTED_MIME_TYPES = (
    SUPPORTED_IMAGE_MIME_TYPES
    + SUPPORTED_DOCUMENT_MIME_TYPES
    + SUPPORTED_VIDEO_MIME_TYPES
    + SUPPORTED_ARCHIVE_MIME_TYPES
)

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


class AttachmentKind(StrEnum):
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    ARCHIVE = "archive"
    OTHER = "other"


_KIND_MIME_PREFIXES: dict[AttachmentKind, tuple[str, ...]] = {
    AttachmentKind.IMAGE: ("image/",),
    AttachmentKind.VIDEO: ("video/",),
}

_KIND_MIME_TYPES: dict[AttachmentKind, tuple[str, ...]] = {
    AttachmentKind.DOCUMENT: tuple(SUPPORTED_DOCUMENT_MIME_TYPES),
    AttachmentKind.ARCHIVE: tuple(SUPPORTED_ARCHIVE_MIME_TYPES),
}

_KIND_EXTENSIONS: dict[AttachmentKind, tuple[str, ...]] = {
    AttachmentKind.IMAGE: tuple(SUPPORTED_IMAGE_EXTENSIONS),
    AttachmentKind.DOCUMENT: tuple(SUPPORTED_DOCUMENT_EXTENSIONS),
    AttachmentKind.VIDEO: tuple(SUPPORTED_VIDEO_EXTENSIONS),
    AttachmentKind.ARCHIVE: tuple(SUPPORTED_ARCHIVE_EXTENSIONS),
}


def detect_attachment_kind(file_type: str | None, extension: str | None) -> AttachmentKind:
    """Infer a high-level attachment kind from MIME type or extension."""
    normalized_type = (file_type or "").lower()
    normalized_ext = (extension or "").lower()

    for kind, prefixes in _KIND_MIME_PREFIXES.items():
        if any(normalized_type.startswith(prefix) for prefix in prefixes if normalized_type):
            return kind

    for kind, mime_types in _KIND_MIME_TYPES.items():
        if normalized_type in mime_types:
            return kind

    if normalized_ext:
        for kind, extensions in _KIND_EXTENSIONS.items():
            if normalized_ext in extensions:
                return kind

    if normalized_type.startswith("application/"):
        return AttachmentKind.DOCUMENT

    return AttachmentKind.OTHER
