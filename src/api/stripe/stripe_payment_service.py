"""Stripe payment service for license invoicing."""

from api.license import License, LicenseUpdate, license_service
from api.tenant import Tenant, tenant_service
from config import get_settings
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from services.email import email_service
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
            try:
                customer = self.stripe.customers.retrieve(tenant.stripe_id)
                updates: dict = {}
                if tenant.email and getattr(customer, "email", None) != tenant.email:
                    updates["email"] = tenant.email
                if tenant.sub_domain and getattr(customer, "name", None) != tenant.sub_domain:
                    updates["name"] = tenant.sub_domain
                if updates:
                    self.stripe.customers.update(customer.id, updates)
            except Exception:
                pass
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
        """Create Stripe invoice for license and send email notification."""
        tenant      : Tenant = await tenant_service.get_tenant_by_id(db, license.tenant_id)
        tenant_email: Optional[str] = tenant.email
        tenant_name : Optional[str] = tenant.sub_domain
        customer_id : str    = await self.ensure_stripe_customer(db, tenant)
        price        = Decimal(str(license.price or 0))
        seats        = max(1, int(license.seats or 1))
        amount_cents = int((price * Decimal(seats) * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        metadata     = {"license_id": str(license.id), "tenant_id": str(tenant.tenant_id)}
        idempotency_base = f"license:{license.id}:amount:{amount_cents}:cur:{self.currency}"

        self.stripe.invoice_items.create({
            "customer"   : customer_id,
            "amount"     : amount_cents,
            "currency"   : self.currency,
            "description": f"License {license.name} ({license.seats} seats)",
            "metadata"   : metadata,
        }, {"idempotency_key": f"invoice_item:{idempotency_base}"})

        invoice = self.stripe.invoices.create({
            "customer"                      : customer_id,
            "collection_method"             : "send_invoice",
            "days_until_due"                : self.days_until_due,
            "auto_advance"                  : False,
            "pending_invoice_items_behavior": "include",
            "metadata"                      : metadata,
        }, {"idempotency_key": f"invoice:{idempotency_base}"})

        # Manually finalize without triggering Stripe's automatic email
        finalized = self.stripe.invoices.finalize_invoice(invoice.id, {"auto_advance": False})

        # Store invoice metadata
        meta: dict = license.meta or {}
        meta.update(
            {
                "stripe_invoice_id" : finalized.id,
                "hosted_invoice_url": finalized.hosted_invoice_url,
                "invoice_pdf"       : finalized.invoice_pdf,
                "amount_cents"      : amount_cents,
                "currency"          : self.currency,
            }
        )

        await license_service.update(db, license.id, LicenseUpdate(meta=meta))

        # Send invoice email via resend
        if finalized.status == "open" and tenant_email:
            due_date = datetime.now() + timedelta(days=self.days_until_due)
            amount_display = f"{price * Decimal(seats):.2f}"

            try:
                await email_service.send_invoice_email(
                    to              = tenant_email,
                    customer_name   = tenant_name or "Customer",
                    invoice_url     = finalized.hosted_invoice_url,
                    amount          = amount_display,
                    currency        = self.currency,
                    due_date        = due_date.strftime("%B %d, %Y"),
                    invoice_number  = finalized.number or finalized.id,
                    invoice_pdf_url = finalized.invoice_pdf or "",
                    license_name    = license.name,
                    license_seats   = seats,
                )
            except Exception as e:
                from observability.logger import get_logger
                logger = get_logger()
                logger.error(f"Failed to send invoice email: {e}")

        return {"invoice_id": finalized.id, "hosted_invoice_url": finalized.hosted_invoice_url}


    async def process_invoice_flow(self, db: AsyncSession, license_id: UUID) -> dict:
        """Process invoice flow: check status and create/return invoice."""
        license: License = await license_service.get_by_id(db, license_id)

        if license.status == "active":
            return {
                "code"   : "already_active",
                "payload": license
                }

        meta: dict = license.meta or {}
        existing_invoice_id: Optional[str] = meta.get("stripe_invoice_id")

        if existing_invoice_id:
            invoice = self.stripe.invoices.retrieve(existing_invoice_id)

            if invoice.status == "paid":
                updated: License = await license_service.activate_license(db, license_id)
                return {"code": "activated", "payload": updated}

            return {
                "code": "invoice_pending",
                "payload": {
                    "invoice_id"        : existing_invoice_id,
                    "hosted_invoice_url": invoice.hosted_invoice_url or meta.get("hosted_invoice_url"),
                    "status"            : invoice.status,
                    "paid"              : (invoice.status == "paid"),
                },
            }

        created: dict = await self.create_invoice_for_license(db, license)
        return {"code": "invoice_created", "payload": created}


stripe_payment_service = StripePaymentService()
