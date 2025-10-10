"""Stripe payment service for license invoicing."""

from api.license import License, LicenseUpdate, license_service
from api.tenant import Tenant, tenant_service
from config import get_settings
from constants import LicenseStatus
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from services.email import email_service
from sqlalchemy import update
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
        self.default_extension_days: int = settings.LICENSE_TERM_DAYS_DEFAULT


    def _get_license_meta_dict(self, license: License) -> dict:
        """Get license metadata as a mutable dictionary."""
        return dict(license.meta or {})


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

        await db.execute(
            update(Tenant)
            .where(Tenant.tenant_id == tenant.tenant_id)
            .values(stripe_id=customer.id)
        )
        await db.commit()

        tenant.stripe_id = customer.id
        return customer.id


    async def create_invoice_for_license(
        self,
        db            : AsyncSession,
        license       : License,
        extension_days: Optional[int] = None,
    ) -> dict:
        """Create Stripe invoice for license and send email notification."""
        tenant      : Tenant = await tenant_service.get_tenant_by_id(db, license.tenant_id)
        tenant_email: Optional[str] = tenant.email
        tenant_name : Optional[str] = tenant.sub_domain
        customer_id : str    = await self.ensure_stripe_customer(db, tenant)

        price        = Decimal(str(license.price or 0))
        seats        = max(1, int(license.seats or 1))
        amount_cents = int((price * Decimal(seats) * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        metadata     = {"license_id": str(license.id), "tenant_id": str(tenant.tenant_id)}

        if extension_days is not None:
            metadata["extension_days"] = str(extension_days)
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
        meta: dict = self._get_license_meta_dict(license)
        meta.update({
            "stripe_invoice_id" : finalized.id,
            "hosted_invoice_url": finalized.hosted_invoice_url,
            "invoice_pdf"       : finalized.invoice_pdf,
            "amount_cents"      : amount_cents,
            "currency"          : self.currency,
        })

        if extension_days is not None:
            meta["pending_extension_days"] = extension_days

        await license_service.update(db, license.id, LicenseUpdate(meta=meta))

        # Send invoice email via resend
        if finalized.status == "open" and tenant_email:
            due_date = datetime.now(timezone.utc) + timedelta(days=self.days_until_due)
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


    async def _activate_license_with_extension(
        self,
        db            : AsyncSession,
        license_obj   : License,
        extension_days: Optional[int] = None,
    ) -> License:
        """Apply activation updates, extending license duration when required."""
        # Get fresh license data
        license_record: License = await license_service.get_by_id(db, license_obj.id)
        meta = self._get_license_meta_dict(license_record)
        stored_extension = meta.pop("pending_extension_days", None)

        # Determine final extension days
        pending_extension = self._resolve_extension_days(extension_days, stored_extension)

        # Calculate actual extension from now
        actual_extension: Optional[int] = None
        if pending_extension is not None:
            actual_extension = self._calculate_extension_from_now(license_record, pending_extension)

        # Use the centralized activation method
        return await license_service.activate_license(
            db,
            license_record.id,
            extension_days=actual_extension,
            meta_updates=meta if meta != self._get_license_meta_dict(license_record) else None,
        )


    def _resolve_extension_days(
        self, requested: int | None, stored: int | str | None
    ) -> int | None:
        """Resolve extension days from requested value or stored metadata."""
        if requested is not None:
            return requested

        if stored is not None:
            try:
                return int(stored)
            except (TypeError, ValueError):
                pass

        return None


    def _calculate_extension_from_now(self, license: License, extension_days: int) -> int:
        """Calculate extension days from current time considering existing end date."""
        now = datetime.now(timezone.utc)
        base = license.ends_at if license.ends_at and license.ends_at > now else now
        new_ends_at = base + timedelta(days=extension_days)
        # Return days from now to new end date
        return (new_ends_at - now).days


    async def process_invoice_flow(
        self,
        db            : AsyncSession,
        license_id    : UUID,
        extension_days: Optional[int] = None,
    ) -> dict:
        """Process invoice flow: check status and create/return invoice."""
        license: License = await license_service.get_by_id(db, license_id)

        # If already active and no extension requested, nothing to do
        if license.status == LicenseStatus.ACTIVE.value and extension_days is None:
            return {"code": "already_active", "payload": license}

        meta: dict = self._get_license_meta_dict(license)
        existing_invoice_id: Optional[str] = meta.get("stripe_invoice_id")

        # Store pending extension if provided and different from current
        if extension_days is not None and meta.get("pending_extension_days") != extension_days:
            meta["pending_extension_days"] = extension_days
            license = await license_service.update(db, license_id, LicenseUpdate(meta=meta))
            meta    = self._get_license_meta_dict(license)
            existing_invoice_id = meta.get("stripe_invoice_id")

        if existing_invoice_id:
            invoice = self.stripe.invoices.retrieve(existing_invoice_id)

            if invoice.status == "paid":
                updated = await self._activate_license_with_extension(db, license, extension_days)
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

        created: dict = await self.create_invoice_for_license(db, license, extension_days)
        return {"code": "invoice_created", "payload": created}


stripe_payment_service = StripePaymentService()
