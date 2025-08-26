from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from api.common import get_current_tenant
from api.tenant.schema import TenantCreate, TenantResponse, TenantUpdate
from api.tenant.service import tenant_service
from database import get_default_db_session
from web import ResponseFactory

routes = APIRouter(
    tags=["tenant"],
    prefix="/tenant",
)

@routes.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant_data: TenantCreate, db: AsyncSession = Depends(get_default_db_session)):
    """Create new tenant"""
    tenant = await tenant_service.create_tenant(db, tenant_data)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse, "created")

@routes.get("/")
async def get_current_tenant_endpoint(tenant=Depends(get_current_tenant)):
    """Get the current tenant"""
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)

@routes.get("/{tenant_id}")
async def get_tenant_by_id(tenant_id: UUID, db: AsyncSession = Depends(get_default_db_session)):
    """Get tenant by ID"""
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)

@routes.get("/subdomain/{subdomain}")
async def get_tenant_by_subdomain(subdomain: str, db: AsyncSession = Depends(get_default_db_session)):
    """Get tenant by subdomain"""
    tenant = await tenant_service.get_tenant_by_subdomain(db, subdomain)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)

@routes.put("/")
async def update_tenant(
    tenant_data: TenantUpdate, tenant=Depends(get_current_tenant), db: AsyncSession = Depends(get_default_db_session)
):
    """Update tenant"""
    updated_tenant = await tenant_service.update_tenant(db, tenant, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)

@routes.put("/{tenant_id}")
async def update_tenant_by_id(
    tenant_id: UUID, tenant_data: TenantUpdate, db: AsyncSession = Depends(get_default_db_session)
):
    """Update tenant by ID"""
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)

@routes.put("/subdomain/{subdomain}")
async def update_tenant_by_subdomain(
    subdomain: str, tenant_data: TenantUpdate, db: AsyncSession = Depends(get_default_db_session)
):
    """Update tenant by subdomain"""
    updated_tenant = await tenant_service.update_tenant_by_subdomain(db, subdomain, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)

@routes.delete("/")
async def delete_tenant(tenant=Depends(get_current_tenant), db: AsyncSession = Depends(get_default_db_session)):
    """Delete tenant"""
    await tenant_service.delete_tenant(db, tenant)
    return ResponseFactory.deleted()

@routes.delete("/{tenant_id}")
async def delete_tenant_by_id(tenant_id: UUID, db: AsyncSession = Depends(get_default_db_session)):
    """Delete tenant by ID"""
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return ResponseFactory.deleted()

@routes.delete("/subdomain/{subdomain}")
async def delete_tenant_by_subdomain(subdomain: str, db: AsyncSession = Depends(get_default_db_session)):
    """Delete tenant by subdomain"""
    await tenant_service.delete_tenant_by_subdomain(db, subdomain)
    return ResponseFactory.deleted()
