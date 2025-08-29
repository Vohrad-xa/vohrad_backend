from api.common import get_tenant_context
from api.common.base_router import BaseRouterMixin
from api.user.schema import UserCreate
from api.user.schema import UserPasswordUpdate
from api.user.schema import UserResponse
from api.user.schema import UserUpdate
from api.user.service import user_service
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from uuid import UUID
from web import DeletedResponse
from web import PaginationParams
from web import ResponseFactory
from web import pagination_params

routes = APIRouter(
    tags=["users"],
    prefix="/users",
)


@routes.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    context=Depends(get_tenant_context),
):
    """Create new user"""
    _, tenant, db = context
    user = await user_service.create_user(db, user_data, tenant)
    return ResponseFactory.transform_and_respond(user, UserResponse, "created")


@routes.get("/search")
async def search_users(
    q: str = Query(..., min_length=2, description="Search term"),
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Search users by email, first name, or last name"""
    _, tenant, db = context
    users, total = await user_service.search_users(db, q, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(users, total, pagination, UserResponse)


@routes.get("/email/{email}")
async def get_user_by_email(
    email: str,
    context=Depends(get_tenant_context),
):
    """Get user by email"""
    _, tenant, db = context
    user = await user_service.get_user_by_email(db, email, tenant)
    if not user:
        from exceptions import user_not_found

        raise user_not_found(email)
    return ResponseFactory.transform_and_respond(user, UserResponse)


@routes.get("/{user_id}")
async def get_user(
    user_id: UUID,
    context=Depends(get_tenant_context),
):
    """Get user by ID"""
    _, tenant, db = context
    user = await user_service.get_user_by_id(db, user_id, tenant)
    return ResponseFactory.transform_and_respond(user, UserResponse)


@routes.get("/")
async def get_users(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get paginated list of users"""
    _, tenant, db = context
    users, total = await user_service.get_users_paginated(db, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(users, total, pagination, UserResponse)


@routes.put("/{user_id}")
async def update_user(
    user_id  : UUID,
    user_data: UserUpdate,
    context=Depends(get_tenant_context),
):
    """Update user"""
    _, tenant, db = context
    user = await user_service.update_user(db, user_id, user_data, tenant)
    return ResponseFactory.transform_and_respond(user, UserResponse)


@routes.put("/{user_id}/password")
async def update_user_password(
    user_id      : UUID,
    password_data: UserPasswordUpdate,
    context=Depends(get_tenant_context),
):
    """Update user password"""
    _, tenant, db = context
    user = await user_service.update_user_password(db, user_id, password_data, tenant)
    return ResponseFactory.transform_and_respond(user, UserResponse)


@routes.put("/{user_id}/verify-email")
async def verify_user_email(
    user_id: UUID,
    context=Depends(get_tenant_context),
):
    """Mark user email as verified"""
    _, tenant, db = context
    user = await user_service.verify_user_email(db, user_id, tenant)
    return ResponseFactory.transform_and_respond(user, UserResponse)


@routes.delete("/{user_id}", response_model=DeletedResponse)
async def delete_user(
    user_id: UUID,
    context=Depends(get_tenant_context),
):
    """Remove user"""
    _, tenant, db = context
    await user_service.delete_user(db, user_id, tenant)
    return DeletedResponse()
