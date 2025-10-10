"""Send license expiry reminders to tenants."""

from api.license import License
from api.tenant.models import Tenant
import asyncio
from commands import CLIStyler, MessageType
from config import get_settings
from constants import LicenseStatus
from database.sessions import with_default_db
from datetime import datetime, timezone
from services.email import email_service
from sqlalchemy import func, select, update
from typing import Optional

REMINDER_WINDOWS = (14, 7, 1)

styler = CLIStyler()


async def _send_expiry_reminders_async() -> None:
    """Locate licenses nearing expiry and send reminder emails."""
    settings        = get_settings()
    now             = datetime.now()
    total_processed = 0
    total_sent      = 0

    styler.print_clean_header("License Expiry Reminders")
    styler.print_clean_message("Scanning licenses for upcoming expirations...", MessageType.STEP)

    async with with_default_db() as db:
        result = await db.execute(
            select(
                License.id,
                License.name,
                License.license_key,
                License.ends_at,
                License.meta,
                Tenant.tenant_id,
                Tenant.email,
                Tenant.sub_domain,
            )
            .join(Tenant, Tenant.tenant_id == License.tenant_id)
            .where(License.status == LicenseStatus.ACTIVE.value)
        )
        rows = result.all()

        updates_applied = False

        for (
            license_id,
            license_name,
            license_key,
            ends_at,
            meta,
            tenant_id,
            tenant_email,
            tenant_name,
        ) in rows:
            if not ends_at or not tenant_email:
                continue

            days_remaining = (ends_at.date() - now.date()).days
            if days_remaining < 0:
                continue

            meta = dict(meta or {})
            sent_registry = dict(meta.get("expiry_reminders_sent") or {})
            reminder_window: Optional[int] = None
            for window in REMINDER_WINDOWS:
                key = str(window)
                if days_remaining <= window and key not in sent_registry:
                    reminder_window = window
                    registry_key = key
                    break

            if reminder_window is None:
                continue

            renew_url: Optional[str] = None
            if settings.LICENSE_RENEW_URL_TEMPLATE:
                renew_url = settings.LICENSE_RENEW_URL_TEMPLATE.format(
                    tenant_id   = str(tenant_id),
                    license_id  = str(license_id),
                    license_key = license_key,
                )

            try:
                await email_service.send_license_expiry_reminder_email(
                    to             = tenant_email,
                    customer_name  = tenant_name or "Customer",
                    license_name   = license_name,
                    expires_on     = ends_at.strftime("%B %d, %Y"),
                    days_remaining = reminder_window,
                    renew_url      = renew_url,
                )
                sent_registry[registry_key] = datetime.now(timezone.utc)
                meta["expiry_reminders_sent"] = sent_registry
                await db.execute(
                    update(License)
                    .where(License.id == license_id)
                    .values(meta=meta, updated_at=func.now())
                )
                updates_applied = True
                total_sent += 1
            except Exception as exc:
                styler.print_clean_message(
                    f"Failed to send reminder for tenant {tenant_name}: {exc}",
                    MessageType.ERROR,
                )

            total_processed += 1

        if updates_applied:
            await db.commit()

    styler.print_clean_message(
        f"Completed reminder scan. Processed {total_processed} licenses, sent {total_sent} reminder(s).",
        MessageType.SUCCESS if total_sent else MessageType.INFO,
    )


def send_expiry_reminders() -> None:
    """Synchronous wrapper for the async reminder sender."""
    asyncio.run(_send_expiry_reminders_async())


if __name__ == "__main__":
    send_expiry_reminders()
