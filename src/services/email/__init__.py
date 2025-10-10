"""Email service for sending emails via Resend."""

from .email_service import EmailService, email_service
from .templates import EmailTemplate

__all__ = ["EmailService", "EmailTemplate", "email_service"]
