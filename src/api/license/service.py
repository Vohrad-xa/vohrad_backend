"""License service with seat validation and key generation."""

from .models import License
from .schema import LicenseCreate, LicenseUpdate
from api.common import BaseService
from api.tenant.models import Tenant
from constants import LicenseStatus
from database import constraint_handler, with_tenant_db
from datetime import datetime
from exceptions import ExceptionFactory
import random
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from string import ascii_uppercase, digits
from typing import NoReturn, Optional
from uuid import UUID


class LicenseService(BaseService[License, LicenseCreate, LicenseUpdate]):
    """License operations with seat validation."""

    def __init__(self):
        super().__init__(License)

    def get_search_fields(self) -> list[str]:
        return ["name", "license_key"]


    async def create_license(self, db: AsyncSession, license_data: LicenseCreate) -> License:
        """Create license with auto-generated license key."""
        try:
            license_key: str = await self._generate_unique_license_key(db)
            license_dict: dict = license_data.model_dump()
            license_dict["license_key"] = license_key

            license: License = License(**license_dict)
            db.add(license)
            await db.commit()
            await db.refresh(license)
            return license

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {"operation": "create_license", "tenant_id": license_data.tenant_id})


    async def activate_license(self, db: AsyncSession, license_id: UUID) -> License:
        """Activate a license and set it as tenant's current license."""
        license: License = await self.get_by_id(db, license_id)

        update_data: dict = {"status": LicenseStatus.ACTIVE.value}
        if not license.starts_at or license.starts_at > datetime.now():
            update_data["starts_at"] = datetime.now()

        updated_license: License = await self.update(db, license_id, LicenseUpdate(**update_data))

        tenant_query = select(Tenant).where(Tenant.tenant_id == license.tenant_id)
        result = await db.execute(tenant_query)
        tenant: Optional[Tenant] = result.scalar_one_or_none()

        if tenant:
            tenant.license_id = license_id
            await db.commit()

        return updated_license


    async def suspend_license(self, db: AsyncSession, license_id: UUID) -> License:
        """Suspend a license and remove it from tenant."""
        updated_license: License = await self.update(db, license_id, LicenseUpdate(status=LicenseStatus.SUSPENDED.value))

        tenant_query = select(Tenant).where(Tenant.license_id == license_id)
        result = await db.execute(tenant_query)
        tenant: Optional[Tenant] = result.scalar_one_or_none()

        if tenant:
            tenant.license_id = None
            await db.commit()

        return updated_license


    async def expire_license(self, db: AsyncSession, license_id: UUID) -> License:
        """Expire a license and remove it from tenant."""
        updated_license: License = await self.update(
            db,
            license_id,
            LicenseUpdate(status=LicenseStatus.EXPIRED.value, ends_at=datetime.now()),
        )

        tenant_query = select(Tenant).where(Tenant.license_id == license_id)
        result = await db.execute(tenant_query)
        tenant: Optional[Tenant] = result.scalar_one_or_none()

        if tenant:
            tenant.license_id = None
            await db.commit()

        return updated_license


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


    def _is_license_active(self, license: License) -> bool:
        """Check if license is currently active."""
        if license.status != LicenseStatus.ACTIVE.value:
            return False

        now = datetime.now()

        if license.starts_at and license.starts_at > now:
            return False

        if license.ends_at and license.ends_at < now:
            return False

        return True


    async def _count_tenant_users(self, tenant: Tenant) -> int:
        """Count active users in tenant schema."""
        from api.user.models import User
        async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
            result = await tenant_db.execute(select(func.count(User.id)).where(User.tenant_id == tenant.tenant_id))
            return result.scalar() or 0


    async def _generate_unique_license_key(self, db: AsyncSession) -> str:
        """Generate unique license key (format: LIC-XXXXXXXXXXXXXXXX)."""
        max_attempts = 10
        for _ in range(max_attempts):
            chars = ascii_uppercase + digits
            random_part = "".join(random.choices(chars, k=16))
            license_key = f"LIC-{random_part}"
            # Check if unique
            result = await db.execute(select(License).where(License.license_key == license_key))
            if not result.scalar_one_or_none():
                return license_key

        raise ExceptionFactory.business_rule("Failed to generate unique license key after 10 attempts")


    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


license_service = LicenseService()
