"""System monitoring and health check endpoints."""

from config.keys import get_key_manager
from fastapi import APIRouter
from services import get_tenant_schema_service

routes = APIRouter(tags=["system"], prefix="/system")


@routes.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "vohrad-api"}


@routes.get("/cache/stats")
async def cache_statistics():
    """Get tenant cache performance statistics."""
    tenant_service = get_tenant_schema_service()
    stats          = await tenant_service.get_cache_performance()
    return {"cache_type": "tenant_schema", "statistics": stats}


@routes.post("/cache/clear")
async def clear_cache():
    """Clear tenant schema cache (admin operation)."""
    tenant_service = get_tenant_schema_service()
    await tenant_service.clear_cache()
    return {"message": "Tenant cache cleared successfully"}


@routes.get("/security/status")
async def security_status():
    """Get security configuration status."""
    key_manager = get_key_manager()
    return {"security_status": key_manager.validate_keys(), "encryption_available": True}
