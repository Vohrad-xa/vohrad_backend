"""Stripe payment service for license invoicing."""

from api.license import License, LicenseUpdate, license_service
from api.tenant import Tenant, tenant_service
from config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
from typing import Optional
from uuid import UUID


class StripePaymentService:
    """Handle Stripe invoice creation and payment processing."""

    def __init__(self):
        settings = get_settings()
        self.stripe = stripe.StripeClient(settings.STRIPE_SECRET_KEY)
        self.currency: str = settings.STRIPE_CURRENCY
        self.days_until_due: int = settings.STRIPE_DAYS_UNTIL_DUE


    async def ensure_stripe_customer(self, db: AsyncSession, tenant: Tenant) -> str:
        """Ensure tenant has a Stripe customer ID, create if missing."""
        if tenant.stripe_id:
            return tenant.stripe_id

        customer = self.stripe.customers.create({
            "name"    : tenant.sub_domain,
            "email"   : tenant.email,
            "metadata": {"tenant_id": str(tenant.tenant_id)},
        })

        from sqlalchemy import update
        await db.execute(
            update(Tenant)
            .where(Tenant.tenant_id == tenant.tenant_id)
            .values(stripe_id=customer.id)
        )
        await db.commit()

        tenant.stripe_id = customer.id
        return customer.id


    async def create_invoice_for_license(self, db: AsyncSession, license: License) -> dict:
        """Create and send Stripe invoice for license."""
        tenant: Tenant = await tenant_service.get_tenant_by_id(db, license.tenant_id)
        customer_id: str = await self.ensure_stripe_customer(db, tenant)
        amount_cents: int = round(float(license.price or 0) * 100) * max(1, license.seats)
        metadata: dict = {"license_id": str(license.id), "tenant_id": str(tenant.tenant_id)}

        self.stripe.invoice_items.create({
            "customer"   : customer_id,
            "amount"     : amount_cents,
            "currency"   : self.currency,
            "description": f"License {license.name} ({license.seats} seats)",
            "metadata"   : metadata,
        })

        invoice = self.stripe.invoices.create({
            "customer"                      : customer_id,
            "collection_method"             : "send_invoice",
            "days_until_due"                : self.days_until_due,
            "pending_invoice_items_behavior": "include",
            "metadata"                      : metadata,
        })

        finalized = self.stripe.invoices.finalize_invoice(invoice.id)

        if finalized.status == "open":
            self.stripe.invoices.send_invoice(finalized.id)

        meta: dict = license.meta or {}
        meta.update(
            {
                "stripe_invoice_id" : finalized.id,
                "hosted_invoice_url": finalized.hosted_invoice_url,
                "amount_cents"      : amount_cents,
                "currency"          : self.currency,
            }
        )

        await license_service.update(db, license.id, LicenseUpdate(meta=meta))

        return {"invoice_id": finalized.id, "hosted_invoice_url": finalized.hosted_invoice_url}


    async def process_invoice_flow(self, db: AsyncSession, license_id: UUID) -> dict:
        """Process invoice flow: check status and create/return invoice."""
        license: License = await license_service.get_by_id(db, license_id)

        if license.status == "active":
            return {"code": "already_active", "payload": license}

        meta: dict = license.meta or {}
        existing_invoice_id: Optional[str] = meta.get("stripe_invoice_id")

        if existing_invoice_id:
            invoice = self.stripe.invoices.retrieve(existing_invoice_id)

            if invoice.status == "paid" or invoice.paid is True:
                updated: License = await license_service.activate_license(db, license_id)
                return {"code": "activated", "payload": updated}

            return {
                "code": "invoice_pending",
                "payload": {
                    "invoice_id"        : existing_invoice_id,
                    "hosted_invoice_url": invoice.hosted_invoice_url or meta.get("hosted_invoice_url"),
                    "status"            : invoice.status,
                    "paid"              : invoice.paid or False,
                },
            }

        created: dict = await self.create_invoice_for_license(db, license)
        return {"code": "invoice_created", "payload": created}


stripe_payment_service = StripePaymentService()
