"""Attachment API module."""

from api.attachment.models import Attachable, Attachment
from api.attachment.service import attachment_service

__all__ = [
    "Attachable",
    "Attachment",
    "attachment_service",
]
