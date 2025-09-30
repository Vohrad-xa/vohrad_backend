"""Tenant service."""

from api.common import BaseService
from api.tenant.models import Tenant
from api.tenant.schema import TenantCreate, TenantUpdate
from database.constraint_handler import constraint_handler
from datetime import time as dtime
from exceptions import tenant_not_found
from security.policy.time_utils import time_to_minutes
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from uuid import UUID


class TenantService(BaseService[Tenant, TenantCreate, TenantUpdate]):
    """Tenant operations."""

    def __init__(self):
        super().__init__(Tenant)


    def get_search_fields(self) -> list[str]:
        return ["sub_domain", "email", "city", "industry"]


    async def create_tenant(self, db: AsyncSession, tenant_data: TenantCreate) -> Tenant:
        try:
            tenant_dict = tenant_data.model_dump()
            tenant_dict["tenant_schema_name"] = tenant_data.sub_domain

            tenant = Tenant(**tenant_dict)
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)
            return tenant

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {
                "operation": "create_tenant",
                "subdomain": tenant_data.sub_domain
            })


    async def get_tenant_by_id(self, db: AsyncSession, tenant_id: UUID) -> Tenant:
        """Get tenant by ID."""
        result = await db.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise tenant_not_found(tenant_id)
        return tenant


    async def get_tenant_by_subdomain(self, db: AsyncSession, subdomain: str) -> Tenant:
        """Get tenant by subdomain."""
        result = await db.execute(select(Tenant).where(Tenant.sub_domain == subdomain))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise tenant_not_found(subdomain)
        return tenant


    async def update_tenant_by_id(
        self,
        db         : AsyncSession,
        tenant_id  : UUID,
        tenant_data: TenantUpdate
    ) -> Tenant:
        """Update tenant by ID."""
        tenant = await self.get_tenant_by_id(db, tenant_id)

        try:
            update_data = tenant_data.model_dump(exclude_unset=True)
            # Normalize time fields to minutes since midnight
            if "business_hour_start" in update_data and isinstance(update_data["business_hour_start"], dtime):
                update_data["business_hour_start"] = time_to_minutes(update_data["business_hour_start"])
            if "business_hour_end" in update_data and isinstance(update_data["business_hour_end"], dtime):
                update_data["business_hour_end"] = time_to_minutes(update_data["business_hour_end"])
            for field, value in update_data.items():
                setattr(tenant, field, value)

            await db.commit()
            await db.refresh(tenant)
            return tenant

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {
                    "operation": "update_tenant",
                    "tenant_id": tenant_id,
                    "subdomain": tenant_data.sub_domain
                }
            )


    async def delete_tenant_by_id(self, db: AsyncSession, tenant_id: UUID) -> None:
        """Delete tenant by ID."""
        tenant = await self.get_tenant_by_id(db, tenant_id)
        await db.delete(tenant)
        await db.commit()


    async def update_tenant(
        self,
        db         : AsyncSession,
        tenant     : Tenant,
        tenant_data: TenantUpdate
    ) -> Tenant:
        """Update tenant using instance."""
        try:
            # Merge the tenant instance into the current session
            tenant = await db.merge(tenant)
            update_data = tenant_data.model_dump(exclude_unset=True)
            # Normalize time fields to minutes since midnight
            if "business_hour_start" in update_data and isinstance(update_data["business_hour_start"], dtime):
                update_data["business_hour_start"] = time_to_minutes(update_data["business_hour_start"])
            if "business_hour_end" in update_data and isinstance(update_data["business_hour_end"], dtime):
                update_data["business_hour_end"] = time_to_minutes(update_data["business_hour_end"])
            for field, value in update_data.items():
                setattr(tenant, field, value)

            await db.commit()
            await db.refresh(tenant)
            return tenant

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {
                    "operation": "update_tenant",
                    "tenant_id": tenant.tenant_id,
                    "subdomain": tenant_data.sub_domain
                }
            )


    async def delete_tenant(self, db: AsyncSession, tenant: Tenant) -> None:
        """Delete tenant using instance."""
        await db.delete(tenant)
        await db.commit()


    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> None:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


tenant_service = TenantService()
