"""Webhook service for handling Stripe payment events."""

from api.license import License, LicenseUpdate, license_service
from api.tenant import Tenant, tenant_service
from constants import LicenseStatus
from database.sessions import with_default_db
from datetime import datetime
from services.email import email_service
from sqlalchemy import select, update
from typing import Optional


class WebhookService:
    """Handle Stripe webhook events."""

    def _extract_invoice_context(self, payload: dict) -> tuple[str, Optional[str]]:
        """Return (invoice_id, customer_id) from invoice or invoice_payment shapes."""
        obj = payload["data"]["object"]
        object_type = obj.get("object")
        if object_type == "invoice_payment":
            return obj.get("invoice"), None
        # Fallback for legacy/standard invoice events
        return obj.get("id") or obj.get("invoice"), obj.get("customer")

    async def handle_payment_succeeded(self, payload: dict) -> bool:
        """Handle invoice.payment_succeeded/invoice.paid and invoice_payment.paid events."""
        invoice_id, _customer_id = self._extract_invoice_context(payload)

        if not invoice_id:
            return True

        async with with_default_db() as db:
            # Authoritative lookup by invoice ID stored in License.meta
            result = await db.execute(
                select(License).where(License.meta["stripe_invoice_id"].astext == invoice_id)
            )
            license: Optional[License] = result.scalar_one_or_none()

            if not license:
                return True

            # Skip if already active (idempotency - prevent duplicate emails)
            if license.status == LicenseStatus.ACTIVE.value:
                return True

            license_id = license.id
            tenant_id = license.tenant_id
            license_name = license.name
            license_key = license.license_key
            license_seats = license.seats

            # Get tenant details for email
            tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
            tenant_email = tenant.email
            tenant_name = tenant.sub_domain

            update_data: dict = {"status": LicenseStatus.ACTIVE.value}
            if not license.starts_at or license.starts_at > datetime.now():
                update_data["starts_at"] = datetime.now()

            await license_service.update(db, license_id, LicenseUpdate(**update_data))
            await db.execute(
                update(Tenant)
                .where(Tenant.tenant_id == tenant_id)
                .values(license_id=license_id)
            )
            await db.commit()

            # Send activation email (only sent once since we check status above)
            if tenant_email:
                try:
                    await email_service.send_license_activation_email(
                        to=tenant_email,
                        customer_name=tenant_name or "Customer",
                        license_name=license_name,
                        license_key=license_key,
                        license_seats=license_seats,
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
        if not invoice_id:
            return True

        async with with_default_db() as db:
            result = await db.execute(
                select(License).where(License.meta["stripe_invoice_id"].astext == invoice_id)
            )
            _license: Optional[License] = result.scalar_one_or_none()
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
            result = await db.execute(
                select(License).where(License.meta["stripe_invoice_id"].astext == invoice_id)
            )
            license: Optional[License] = result.scalar_one_or_none()

            if not license:
                return True

            meta: dict = license.meta or {}
            changed = False
            if hosted_url and meta.get("hosted_invoice_url") != hosted_url:
                meta["hosted_invoice_url"] = hosted_url
                changed = True
            if pdf_url and meta.get("invoice_pdf") != pdf_url:
                meta["invoice_pdf"] = pdf_url
                changed = True

            if changed:
                await license_service.update(db, license.id, LicenseUpdate(meta=meta))
                await db.commit()

        return True


webhook_service = WebhookService()
