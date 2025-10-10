"""Email service for sending emails using Resend."""

from .templates import EmailTemplate
from config import get_settings
from observability.logger import get_logger
import resend
from typing import List, Optional

logger = get_logger()


class EmailService:
    """Service for sending emails via Resend."""

    def __init__(self):
        """Initialize email service with Resend configuration."""
        settings          = get_settings()
        self.api_key      = settings.RESEND_API_KEY
        self.from_address = settings.EMAIL_FROM_ADDRESS
        self.from_name    = settings.EMAIL_FROM_NAME

        if self.api_key:
            resend.api_key = self.api_key
        else:
            logger.warning("RESEND_API_KEY not configured - email sending will fail")

    def _format_from_address(self) -> str:
        """Format the 'from' address with name."""
        return f"{self.from_name} <{self.from_address}>"

    async def send_email(
        self,
        to          : str | List[str],
        subject     : str,
        html        : str,
        from_address: Optional[str] = None,
    ) -> dict:
        """Send an email using Resend."""
        if not self.api_key:
            logger.error("Cannot send email - RESEND_API_KEY not configured")
            raise ValueError("Email service not configured")

        to_list = [to] if isinstance(to, str) else to

        params: resend.Emails.SendParams = {
            "from"   : from_address or self._format_from_address(),
            "to"     : to_list,
            "subject": subject,
            "html"   : html,
        }

        try:
            response = resend.Emails.send(params)
            logger.info(f"Email sent successfully to {to_list}: {response}")
            return {"status": "success", "data": response}
        except Exception as e:
            logger.error(f"Failed to send email to {to_list}: {e}")
            raise

    async def send_invoice_email(
        self,
        to             : str,
        customer_name  : str,
        invoice_url    : str,
        amount         : str,
        currency       : str,
        due_date       : str,
        invoice_number : str,
        invoice_pdf_url: str = "",
        license_name   : str = "",
        license_seats  : int = 0,
    ) -> dict:
        """Send invoice email to customer."""
        subject = f"Invoice {invoice_number} from {self.from_name}"
        html = EmailTemplate.invoice_template(
            customer_name   = customer_name,
            invoice_url     = invoice_url,
            amount          = amount,
            currency        = currency.upper(),
            due_date        = due_date,
            invoice_number  = invoice_number,
            company_name    = self.from_name,
            invoice_pdf_url = invoice_pdf_url,
            license_name    = license_name,
            license_seats   = license_seats,
        )

        return await self.send_email(to=to, subject=subject, html=html)


email_service = EmailService()
