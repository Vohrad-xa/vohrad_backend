"""System monitoring and health check endpoints."""

from api.tenant import get_tenant_schema_resolver
from config.keys import get_key_manager
from fastapi import APIRouter
from web import ResponseFactory, SuccessResponse

routes = APIRouter(tags=["system"], prefix="/system")


@routes.get("/health", response_model=SuccessResponse[dict])
async def health_check():
    """Basic health check endpoint."""
    return ResponseFactory.success({"status": "healthy", "service": "vohrad-api"})


@routes.get("/cache/stats", response_model=SuccessResponse[dict])
async def cache_statistics():
    """Get tenant cache performance statistics."""
    tenant_service = get_tenant_schema_resolver()
    stats          = await tenant_service.get_cache_performance()
    return ResponseFactory.success({"cache_type": "tenant_schema", "statistics": stats})


@routes.post("/cache/clear", response_model=SuccessResponse[dict])
async def clear_cache():
    """Clear tenant schema cache (admin operation)."""
    tenant_service = get_tenant_schema_resolver()
    await tenant_service.clear_cache()
    return ResponseFactory.success({"message": "Tenant cache cleared successfully"})


@routes.get("/security/status", response_model=SuccessResponse[dict])
async def security_status():
    """Get security configuration status."""
    key_manager = get_key_manager()
    return ResponseFactory.success({"security_status": key_manager.validate_keys(), "encryption_available": True})
