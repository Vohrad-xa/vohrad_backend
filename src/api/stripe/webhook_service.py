"""Webhook service for handling Stripe payment events."""

from api.license.models import License
from api.license.schema import LicenseUpdate
from api.license.service import license_service
from api.tenant.models import Tenant
from constants import LicenseStatus
from database.sessions import with_default_db
from datetime import datetime
from exceptions import ExceptionFactory
from sqlalchemy import select, update
from typing import Optional


class WebhookService:
    """Handle Stripe webhook events."""

    async def handle_payment_succeeded(self, payload: dict) -> bool:
        """Handle invoice.payment_succeeded or invoice.paid events."""
        invoice = payload["data"]["object"]
        customer_id: str    = invoice["customer"]
        invoice_id : str    = invoice["id"]

        async with with_default_db() as db:
            tenant_query = select(Tenant).where(Tenant.stripe_id == customer_id)
            result = await db.execute(tenant_query)
            tenant: Optional[Tenant] = result.scalar_one_or_none()

            if not tenant:
                raise ExceptionFactory.business_rule(
                    "Payment succeeded for unknown customer",
                    {"stripe_customer_id": customer_id}
                )

            # Store IDs to avoid lazy loading issues
            tenant_id = tenant.tenant_id

            license_query = (
                select(License)
                .where(License.tenant_id == tenant_id)
                .where(License.meta["stripe_invoice_id"].astext == invoice_id)
            )
            result = await db.execute(license_query)
            license: Optional[License] = result.scalar_one_or_none()

            if license:
                # Store license ID before any operations
                license_id = license.id
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
        return True


    async def handle_payment_failed(self, payload: dict) -> bool:
        """Handle invoice.payment_failed events."""
        invoice = payload["data"]["object"]
        customer_id: str = invoice["customer"]

        async with with_default_db() as db:
            tenant_query = select(Tenant).where(Tenant.stripe_id == customer_id)
            result = await db.execute(tenant_query)
            tenant: Optional[Tenant] = result.scalar_one_or_none()
            if not tenant:
                raise ExceptionFactory.business_rule(
                    "Payment failed for unknown customer",
                    {"stripe_customer_id": customer_id}
                )
        return True


webhook_service = WebhookService()
