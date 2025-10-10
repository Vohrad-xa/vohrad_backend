"""Webhook service for handling Stripe payment events."""

from .stripe_payment_service import stripe_payment_service
from api.license import License, LicenseUpdate, license_service
from api.tenant import tenant_service
from constants import LicenseStatus
from database.sessions import with_default_db
from services.email import email_service
from sqlalchemy import select
from typing import Optional


class WebhookService:
    """Handle Stripe webhook events."""

    async def _find_license_by_invoice_id(self, db, invoice_id: str) -> Optional[License]:
        """Find license by Stripe invoice ID stored in metadata."""
        if not invoice_id:
            return None

        result = await db.execute(
            select(License).where(License.meta["stripe_invoice_id"].astext == invoice_id)
        )
        return result.scalar_one_or_none()


    def _extract_invoice_context(self, payload: dict) -> tuple[str, Optional[str]]:
        """Return (invoice_id, customer_id) from invoice or invoice_payment shapes."""
        obj = payload["data"]["object"]
        object_type = obj.get("object")
        if object_type == "invoice_payment":
            return obj.get("invoice"), None
        # Fallback for legacy/standard invoice events
        return obj.get("id") or obj.get("invoice"), obj.get("customer")


    def _extract_extension_days(self, payload: dict) -> Optional[int]:
        """Extract extension_days from webhook payload metadata."""
        try:
            metadata = payload.get("data", {}).get("object", {}).get("metadata")
            if metadata and isinstance(metadata, dict):
                value = metadata.get("extension_days")
                return int(value) if value else None
        except (TypeError, ValueError):
            return None
        return None

    async def handle_payment_succeeded(self, payload: dict) -> bool:
        """Handle invoice.payment_succeeded/invoice.paid and invoice_payment.paid events."""
        invoice_id, _customer_id = self._extract_invoice_context(payload)

        async with with_default_db() as db:
            license: Optional[License] = await self._find_license_by_invoice_id(db, invoice_id)

            if not license:
                return True

            # Skip if already active (idempotency - prevent duplicate emails)
            if license.status == LicenseStatus.ACTIVE.value:
                return True

            # Extract data for email notification
            tenant_id     = license.tenant_id
            license_name  = license.name
            license_key   = license.license_key
            license_seats = license.seats

            # Get tenant details for email
            tenant       = await tenant_service.get_tenant_by_id(db, tenant_id)
            tenant_email = tenant.email
            tenant_name  = tenant.sub_domain

            # Extract extension days from webhook metadata
            extension_days = self._extract_extension_days(payload)

            # Activate the license
            await stripe_payment_service._activate_license_with_extension(db, license, extension_days)

            # Send activation email (only sent once since we check status above)
            if tenant_email:
                try:
                    await email_service.send_license_activation_email(
                        to            = tenant_email,
                        customer_name = tenant_name or "Customer",
                        license_name  = license_name,
                        license_key   = license_key,
                        license_seats = license_seats,
                    )
                except Exception as e:
                    from observability.logger import get_logger
                    logger = get_logger()
                    logger.error(f"Failed to send activation email: {e}")

        return True


    async def handle_payment_failed(self, payload: dict) -> bool:
        """Handle invoice.payment_failed and invoice_payment.failed events."""
        invoice_id, _customer_id = self._extract_invoice_context(payload)

        # Nothing to do for failures in this flow, but keep idempotent 200 to avoid retries
        async with with_default_db() as db:
            _license: Optional[License] = await self._find_license_by_invoice_id(db, invoice_id)

        return True

    async def handle_invoice_updated(self, payload: dict) -> bool:
        """Handle invoice.updated: refresh hosted_invoice_url if changed."""
        obj = payload["data"]["object"]
        if obj.get("object") != "invoice":
            return True

        invoice_id: Optional[str] = obj.get("id")
        hosted_url: Optional[str] = obj.get("hosted_invoice_url")
        pdf_url   : Optional[str] = obj.get("invoice_pdf")

        if not invoice_id:
            return True

        async with with_default_db() as db:
            license: Optional[License] = await self._find_license_by_invoice_id(db, invoice_id)

            if not license:
                return True

            # Check if invoice URLs have changed
            meta: dict = dict(license.meta or {})
            updates: dict = {}

            if hosted_url and meta.get("hosted_invoice_url") != hosted_url:
                updates["hosted_invoice_url"] = hosted_url

            if pdf_url and meta.get("invoice_pdf") != pdf_url:
                updates["invoice_pdf"] = pdf_url

            # Only update if there are changes
            if updates:
                meta.update(updates)
                await license_service.update(db, license.id, LicenseUpdate(meta=meta))
                await db.commit()

        return True


webhook_service = WebhookService()
