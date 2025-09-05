from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.permission.dependencies import RequireRoleManagement
from api.role.schema import RoleCreate, RoleResponse, RoleUpdate
from api.role.service import role_service
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import DeletedResponse, PaginationParams, ResponseFactory, pagination_params

routes = APIRouter(
    tags   = ["roles"],
    prefix = "/roles",
)


@routes.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    context      = Depends(get_tenant_context),
    _authorized  = Depends(RequireRoleManagement)
):
    """Create new role"""
    _, _tenant, db = context
    role = await role_service.create_role(db, role_data)
    return ResponseFactory.transform_and_respond(role, RoleResponse, "created")


@routes.get("/search")
async def search_roles(
    q         : str              = Query(..., min_length=2, description="Search term"),
    pagination: PaginationParams = Depends(pagination_params),
               context           = Depends(get_tenant_context),
):
    """Search roles by name or description"""
    _, _tenant, db = context
    roles, total = await role_service.search_roles(db, q, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(roles, total, pagination, RoleResponse)


@routes.get("/active")
async def get_active_roles(
    context=Depends(get_tenant_context),
):
    """Get all active roles"""
    _, _tenant, db = context
    roles = await role_service.get_active_roles(db)

    role_responses = [RoleResponse.model_validate(role) for role in roles]
    return ResponseFactory.success(data=role_responses)


@routes.get("/name/{name}")
async def get_role_by_name(
    name: str,
    context=Depends(get_tenant_context),
):
    """Get role by name"""
    _, _tenant, db = context
    role = await role_service.get_role_by_name(db, name)
    if not role:
        from exceptions import ExceptionFactory

        raise ExceptionFactory.not_found("Role", name)
    return ResponseFactory.transform_and_respond(role, RoleResponse)


@routes.get("/{role_id}")
async def get_role(
    role_id: UUID,
    context=Depends(get_tenant_context),
):
    """Get role by ID"""
    _, _tenant, db = context
    role = await role_service.get_role_by_id(db, role_id)
    return ResponseFactory.transform_and_respond(role, RoleResponse)


@routes.get("/")
async def get_roles(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get paginated list of roles"""
    _, _tenant, db = context
    roles, total = await role_service.get_roles_paginated(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(roles, total, pagination, RoleResponse)


@routes.put("/{role_id}")
async def update_role(
    role_id  : UUID,
    role_data: RoleUpdate,
    context     = Depends(get_tenant_context),
    _authorized = Depends(RequireRoleManagement)
):
    """Update role"""
    _, _tenant, db = context
    role = await role_service.update_role(db, role_id, role_data)
    return ResponseFactory.transform_and_respond(role, RoleResponse)


@routes.put("/{role_id}/activate")
async def activate_role(
    role_id: UUID,
    context=Depends(get_tenant_context),
):
    """Activate role"""
    _, _tenant, db = context
    role = await role_service.activate_role(db, role_id)
    return ResponseFactory.transform_and_respond(role, RoleResponse)


@routes.put("/{role_id}/deactivate")
async def deactivate_role(
    role_id: UUID,
    context = Depends(get_tenant_context),
):
    """Deactivate role"""
    _, _tenant, db = context
    role = await role_service.deactivate_role(db, role_id)
    return ResponseFactory.transform_and_respond(role, RoleResponse)


@routes.delete("/{role_id}", response_model=DeletedResponse)
async def delete_role(
    role_id: UUID,
    context = Depends(get_tenant_context),
    _authorized: bool = Depends(RequireRoleManagement)
):
    """Remove role"""
    _, _tenant, db = context
    await role_service.delete_role(db, role_id)
    return DeletedResponse()
