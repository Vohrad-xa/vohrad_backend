"""License service with seat validation and key generation."""

from .models import License
from .schema import LicenseCreate, LicenseUpdate
from api.common import BaseService
from api.tenant.models import Tenant
from constants import LicenseStatus
from database import constraint_handler, with_tenant_db
from datetime import datetime, timedelta, timezone
from exceptions import ExceptionFactory
import random
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from string import ascii_uppercase, digits
from typing import NoReturn, Optional
from uuid import UUID


class LicenseService(BaseService[License, LicenseCreate, LicenseUpdate]):
    """License operations with seat validation."""

    # License key generation constants
    LICENSE_KEY_PREFIX = "LIC"
    LICENSE_KEY_LENGTH = 16
    LICENSE_KEY_MAX_ATTEMPTS = 10

    def __init__(self):
        super().__init__(License)

    def get_search_fields(self) -> list[str]:
        return ["name", "license_key"]


    async def get_by_id(self, db: AsyncSession, obj_id: UUID, tenant_id: Optional[UUID] = None) -> License:
        """Override to ensure time-boxed licenses auto-expire when fetched."""
        license_obj = await super().get_by_id(db, obj_id, tenant_id)
        return await self._expire_if_past_end(db, license_obj)


    async def create_license(self, db: AsyncSession, license_data: LicenseCreate) -> License:
        """Create license with auto-generated license key."""
        try:
            license_key: str = await self._generate_unique_license_key(db)
            license_dict: dict = license_data.model_dump()
            license_dict["license_key"] = license_key

            license: License = License(**license_dict)
            db.add(license)
            await db.flush()  # Flush to get the ID before suspending others

            # If creating an active license, activate it properly
            if license.status == LicenseStatus.ACTIVE.value:
                await self._suspend_other_active_licenses(db, license.tenant_id, license.id)
                await self._assign_license_to_tenant(db, license.tenant_id, license.id)

            await db.commit()
            await db.refresh(license)
            return license

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {"operation": "create_license", "tenant_id": license_data.tenant_id})


    async def activate_license(
        self,
        db: AsyncSession,
        license_id: UUID,
        extension_days: Optional[int] = None,
        meta_updates: Optional[dict] = None,
    ) -> License:
        """Activate a license and set it as tenant's current license."""
        license: License = await self.get_by_id(db, license_id)
        now = datetime.now(timezone.utc)
        await self._suspend_other_active_licenses(db, license.tenant_id, license_id)
        update_data: dict = {"status": LicenseStatus.ACTIVE.value}

        # Set start date if not already set or in the future
        if not license.starts_at or license.starts_at > now:
            update_data["starts_at"] = now

        # Handle end date extension
        if extension_days is not None:
            base = license.ends_at if license.ends_at and license.ends_at > now else now
            update_data["ends_at"] = base + timedelta(days=extension_days)

        # Apply metadata updates
        if meta_updates is not None:
            update_data["meta"] = meta_updates
        updated_license: License = await self.update(db, license_id, LicenseUpdate(**update_data))
        await self._assign_license_to_tenant(db, license.tenant_id, license_id)
        return updated_license


    async def suspend_license(self, db: AsyncSession, license_id: UUID) -> License:
        """Suspend a license and remove it from tenant."""
        updated_license: License = await self.update(
            db, license_id, LicenseUpdate(status=LicenseStatus.SUSPENDED.value)
        )
        await self._detach_license_from_tenant(db, license_id)
        return updated_license


    async def expire_license(self, db: AsyncSession, license_id: UUID) -> License:
        """Expire a license and remove it from tenant."""
        license_obj: License = await super().get_by_id(db, license_id)
        if license_obj.status == LicenseStatus.EXPIRED.value:
            return license_obj
        return await self._set_status_expired(db, license_obj, datetime.now(timezone.utc))


    async def check_seat_availability(self, db: AsyncSession, tenant: Tenant) -> bool:
        """Check if tenant has available seats for new users."""
        if not tenant.license_id:
            return False  # No license = no seats
        license: License = await self.get_by_id(db, tenant.license_id)
        if not self._is_license_active(license):
            return False
        user_count: int = await self._count_tenant_users(tenant)
        return user_count < license.seats


    async def assert_can_add_user(self, db: AsyncSession, tenant: Tenant) -> None:
        """Raise exception if tenant cannot add more users."""
        if not tenant.license_id:
            raise ExceptionFactory.license_limit_exceeded(tenant_id=tenant.tenant_id, current_users=0, seat_limit=0)

        license: License = await self.get_by_id(db, tenant.license_id)
        if not self._is_license_active(license):
            raise ExceptionFactory.business_rule(
                f"License is {license.status}, cannot add users",
                {"license_id": str(license.id), "status": license.status},
            )
        user_count: int = await self._count_tenant_users(tenant)

        if user_count >= license.seats:
            raise ExceptionFactory.license_limit_exceeded(
                tenant_id=tenant.tenant_id, current_users=user_count, seat_limit=license.seats
            )


    async def get_tenant_license_info(self, db: AsyncSession, tenant: Tenant) -> dict:
        """Get license information for a tenant including seat usage."""
        if not tenant.license_id:
            return {
                "has_license"    : False,
                "license"        : None,
                "seats_used"     : 0,
                "seats_available": 0,
                "seats_total"    : 0,
            }

        license: License = await self.get_by_id(db, tenant.license_id)
        user_count: int = await self._count_tenant_users(tenant)

        return {
            "has_license"    : True,
            "license"        : license,
            "seats_used"     : user_count,
            "seats_available": max(0, license.seats - user_count),
            "seats_total"    : license.seats,
            "is_active"      : self._is_license_active(license),
        }


    def _is_license_active(self, license: License, now: Optional[datetime] = None) -> bool:
        """Check if license is currently active."""
        if license.status != LicenseStatus.ACTIVE.value:
            return False
        if now is None:
            now = datetime.now(timezone.utc)
        if license.starts_at and license.starts_at > now:
            return False
        if license.ends_at and license.ends_at < now:
            return False
        return True


    async def _expire_if_past_end(self, db: AsyncSession, license_obj: License) -> License:
        """Auto-expire the license if the configured end date has elapsed."""
        now = datetime.now(timezone.utc)
        if (
            license_obj.status == LicenseStatus.ACTIVE.value
            and license_obj.ends_at
            and license_obj.ends_at <= now
        ):
            return await self._set_status_expired(db, license_obj, license_obj.ends_at)
        return license_obj


    async def _set_status_expired(
        self,
        db         : AsyncSession,
        license_obj: License,
        ends_at    : datetime,
    ) -> License:
        """Persist the expired status and detach the license from the tenant."""
        await db.execute(
            update(License)
            .where(License.id == license_obj.id)
            .values(
                status    = LicenseStatus.EXPIRED.value,
                ends_at   = ends_at,
                updated_at= func.now(),
            )
        )
        # Detach from tenant
        await self._detach_license_from_tenant(db, license_obj.id)
        await db.commit()
        await db.refresh(license_obj)
        return license_obj


    async def _suspend_other_active_licenses(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        current_license_id: UUID,
    ) -> None:
        """Suspend any other active licenses for the tenant."""
        now = datetime.now(timezone.utc)
        suspend_stmt = (
            update(License)
            .where(
                License.tenant_id == tenant_id,
                License.status == LicenseStatus.ACTIVE.value,
                License.id != current_license_id,
            )
            .values(
                status=LicenseStatus.SUSPENDED.value,
                ends_at=now,
                updated_at=func.now(),
            )
        )

        await db.execute(suspend_stmt)


    async def _assign_license_to_tenant(self, db: AsyncSession, tenant_id: UUID, license_id: UUID) -> None:
        """Assign a license as the tenant's active license."""
        await db.execute(
            update(Tenant)
            .where(Tenant.tenant_id == tenant_id)
            .values(license_id=license_id, updated_at=func.now())
        )
        await db.commit()


    async def _detach_license_from_tenant(self, db: AsyncSession, license_id: UUID) -> None:
        """Remove license assignment from any tenant."""
        await db.execute(
            update(Tenant)
            .where(Tenant.license_id == license_id)
            .values(license_id=None, updated_at=func.now())
        )
        await db.commit()


    async def _count_tenant_users(self, tenant: Tenant) -> int:
        """Count active users in tenant schema."""
        from api.user.models import User
        async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
            result = await tenant_db.execute(select(func.count(User.id)).where(User.tenant_id == tenant.tenant_id))
            return result.scalar() or 0


    async def _generate_unique_license_key(self, db: AsyncSession) -> str:
        """Generate unique license key (format: PREFIX-XXXXXXXXXXXXXXXX)."""
        chars = ascii_uppercase + digits
        for _ in range(self.LICENSE_KEY_MAX_ATTEMPTS):
            random_part = "".join(random.choices(chars, k=self.LICENSE_KEY_LENGTH))
            license_key = f"{self.LICENSE_KEY_PREFIX}-{random_part}"
            # Check if unique
            result = await db.execute(select(License).where(License.license_key == license_key))
            if not result.scalar_one_or_none():
                return license_key

        raise ExceptionFactory.business_rule(
            f"Failed to generate unique license key after {self.LICENSE_KEY_MAX_ATTEMPTS} attempts"
        )


    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


license_service = LicenseService()
