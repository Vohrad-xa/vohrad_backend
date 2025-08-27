from api.tenant.models import Tenant
from api.tenant.schema import TenantCreate
from api.tenant.schema import TenantUpdate
from exceptions import duplicate_subdomain
from exceptions import tenant_not_found
from services import BaseService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class TenantService(BaseService[Tenant, TenantCreate, TenantUpdate]):
    """Service class for tenant business logic"""

    def __init__(self):
        super().__init__(Tenant)

    def get_search_fields(self) -> list[str]:
        """Return searchable fields for tenant."""
        return ["sub_domain", "email", "city", "industry"]

    async def create_tenant(self, db: AsyncSession, tenant_data: TenantCreate) -> Tenant:
        """Create new tenant with subdomain uniqueness check"""
        if await self.exists(db, "sub_domain", tenant_data.sub_domain):
            raise duplicate_subdomain(tenant_data.sub_domain)

        tenant_dict = tenant_data.model_dump()
        tenant_dict["tenant_schema_name"] = tenant_data.sub_domain

        tenant = Tenant(**tenant_dict)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant

    async def get_tenant_by_id(self, db: AsyncSession, tenant_id: int) -> Tenant:
        """Get tenant by ID"""
        result = await db.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise tenant_not_found(tenant_id)
        return tenant

    async def get_tenant_by_subdomain(self, db: AsyncSession, subdomain: str) -> Tenant:
        """Get tenant by subdomain"""
        result = await db.execute(select(Tenant).where(Tenant.sub_domain == subdomain))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise tenant_not_found(subdomain)
        return tenant

    async def update_tenant_by_id(self, db: AsyncSession, tenant_id: int, tenant_data: TenantUpdate) -> Tenant:
        """Update tenant by ID"""
        tenant = await self.get_tenant_by_id(db, tenant_id)

        # Check subdomain uniqueness if being updated
        if tenant_data.sub_domain and tenant_data.sub_domain != tenant.sub_domain:
            if await self.exists(db, "sub_domain", tenant_data.sub_domain, exclude_id=tenant.tenant_id):
                raise duplicate_subdomain(tenant_data.sub_domain)

        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        await db.commit()
        await db.refresh(tenant)
        return tenant

    async def update_tenant_by_subdomain(self, db: AsyncSession, subdomain: str, tenant_data: TenantUpdate) -> Tenant:
        """Update tenant by subdomain"""
        tenant = await self.get_tenant_by_subdomain(db, subdomain)

        # Check subdomain uniqueness if being updated
        if tenant_data.sub_domain and tenant_data.sub_domain != tenant.sub_domain:
            if await self.exists(db, "sub_domain", tenant_data.sub_domain, exclude_id=tenant.tenant_id):
                raise duplicate_subdomain(tenant_data.sub_domain)

        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        await db.commit()
        await db.refresh(tenant)
        return tenant

    async def delete_tenant_by_id(self, db: AsyncSession, tenant_id: int) -> None:
        """Delete tenant by ID"""
        tenant = await self.get_tenant_by_id(db, tenant_id)
        await db.delete(tenant)
        await db.commit()

    async def delete_tenant_by_subdomain(self, db: AsyncSession, subdomain: str) -> None:
        """Delete tenant by subdomain"""
        tenant = await self.get_tenant_by_subdomain(db, subdomain)
        await db.delete(tenant)
        await db.commit()

    async def update_tenant(self, db: AsyncSession, tenant: Tenant, tenant_data: TenantUpdate) -> Tenant:
        """Update tenant - now accepts tenant as a parameter to avoid repeated queries"""
        # Check subdomain uniqueness if being updated
        if tenant_data.sub_domain and tenant_data.sub_domain != tenant.sub_domain:
            if await self.exists(db, "sub_domain", tenant_data.sub_domain, exclude_id=tenant.tenant_id):
                raise duplicate_subdomain(tenant_data.sub_domain)

        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        await db.commit()
        await db.refresh(tenant)
        return tenant

    async def delete_tenant(self, db: AsyncSession, tenant: Tenant) -> None:
        """Delete tenant - now accepts tenant as a parameter to avoid repeated queries"""
        await db.delete(tenant)
        await db.commit()

tenant_service = TenantService()
