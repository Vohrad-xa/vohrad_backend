"""User router."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.permission.dependencies import RequireManager, RequireRoleManagement, require_permission
from api.role.schema import RoleResponse
from api.user.schema import UserCreate, UserPasswordUpdate, UserResponse, UserRoleAssignRequest, UserUpdate
from api.user.service import user_service
from exceptions import user_not_found
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
    pagination_params,
)

routes = APIRouter(
    tags   = ["users"],
    prefix = "/users",
)


@routes.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatedResponse[UserResponse],
)
async def create_user(
    user_data: UserCreate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireManager),
):
    """Create new user"""
    _, tenant, db = context
    user = await user_service.create_user(db, user_data, tenant)
    return ResponseFactory.created(user, response_model=UserResponse)


@routes.get("/search", response_model=SuccessResponse[PaginatedResponse[UserResponse]])
async def search_users(
    q: str = Query(..., min_length=2, description="Search term"),
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireManager),
):
    """Search users by email, first name, or last name"""
    _, tenant, db = context
    users, total = await user_service.search_users(db, q, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(users, total, pagination, UserResponse)


@routes.get("/email/{email}", response_model=SuccessResponse[UserResponse])
async def get_user_by_email(
    email: str,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(require_permission("user", "read")),
):
    """Get user by email"""
    _, tenant, db = context
    user = await user_service.get_user_by_email(db, email, tenant)
    if not user:
        raise user_not_found(email)
    return ResponseFactory.success(user, response_model=UserResponse)


@routes.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(require_permission("user", "read")),
):
    """Get user by ID"""
    _, tenant, db = context
    user = await user_service.get_user_by_id(db, user_id, tenant)
    return ResponseFactory.success(user, response_model=UserResponse)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[UserResponse]])
async def get_users(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireManager),
):
    """Get paginated list of users"""
    _, tenant, db = context
    users, total = await user_service.get_users_paginated(db, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(users, total, pagination, UserResponse)


@routes.put("/{user_id}", response_model=UpdatedResponse[UserResponse])
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(require_permission("user", "update")),
):
    """Update user"""
    _, tenant, db = context
    user = await user_service.update_user(db, user_id, user_data, tenant)
    return ResponseFactory.updated(user, response_model=UserResponse)


@routes.put("/{user_id}/password", response_model=UpdatedResponse[UserResponse])
async def update_user_password(
    user_id: UUID,
    password_data: UserPasswordUpdate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(require_permission("user", "update")),
):
    """Update user password"""
    _, tenant, db = context
    user = await user_service.update_user_password(db, user_id, password_data, tenant)
    return ResponseFactory.updated(user, response_model=UserResponse)


@routes.put("/{user_id}/verify-email", response_model=UpdatedResponse[UserResponse])
async def verify_user_email(
    user_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(require_permission("user", "update")),
):
    """Mark user email as verified"""
    _, tenant, db = context
    user = await user_service.verify_user_email(db, user_id, tenant)
    return ResponseFactory.updated(user, response_model=UserResponse)


@routes.delete("/{user_id}", response_model=DeletedResponse)
async def delete_user(
    user_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireManager),
):
    """Remove user"""
    _, tenant, db = context
    await user_service.delete_user(db, user_id, tenant)
    return ResponseFactory.deleted("user")


@routes.get("/{user_id}/roles", response_model=SuccessResponse[list[RoleResponse]])
async def get_user_roles(
    user_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(require_permission("user", "read")),
):
    """Get roles assigned to user"""
    _, tenant, db = context
    roles = await user_service.get_user_roles(db, user_id, tenant)
    return ResponseFactory.success(roles, response_model=RoleResponse)


@routes.post(
    "/{user_id}/roles",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[dict],
)
async def assign_role_to_user(
    user_id: UUID,
    request: UserRoleAssignRequest,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireRoleManagement),
):
    """Assign role to user"""
    current_user, tenant, db = context
    assignment = await user_service.assign_role_to_user(db, user_id, request.role_id, current_user.user_id, tenant)
    return ResponseFactory.success(
        data={"user_id": str(assignment.user_id), "role_id": str(assignment.role_id)}, message="Role assigned successfully"
    )


@routes.delete("/{user_id}/roles/{role_id}", response_model=DeletedResponse)
async def revoke_role_from_user(
    user_id: UUID,
    role_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireRoleManagement),
):
    """Revoke role from user"""
    _, tenant, db = context
    await user_service.revoke_role_from_user(db, user_id, role_id, tenant)
    return ResponseFactory.deleted("role")
