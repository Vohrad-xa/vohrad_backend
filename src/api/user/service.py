"""User service with caching.

Notes:
- Cache by (user_id/email, tenant_id) with invalidation on updates/deletes.
"""

from api.assignment.models import Assignment
from api.common import BaseService
from api.role.models import Role
from api.tenant.models import Tenant
from api.user.models import User
from api.user.schema import UserCreate, UserPasswordUpdate, UserUpdate
from constants.enums import RoleStage
from database.cache import UserCache
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory, invalid_credentials
from middleware import hash_password, verify_password
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
from uuid import UUID


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """User operations."""

    def __init__(self):
        super().__init__(User)
        self.user_cache = UserCache()


    def get_search_fields(self) -> list[str]:
        return ["email", "first_name", "last_name", "city"]


    async def create_user(self, db: AsyncSession, user_data: UserCreate, tenant: Tenant) -> User:
        try:
            hashed_password = hash_password(user_data.password)
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["password"] = hashed_password
            user_dict["tenant_id"] = tenant.tenant_id

            user = User(**user_dict)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {"operation": "create_user", "email": user_data.email, "tenant_id": tenant.tenant_id}
            )


    async def get_user_by_id(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> User:
        cached_user = await self.user_cache.get_user_by_id(user_id, tenant.tenant_id)
        if cached_user:
            return cached_user

        user = await self.get_by_id(db, user_id, tenant.tenant_id)
        if user:
            await self.user_cache.cache_user(user, tenant.tenant_id)
        return user


    async def get_user_by_email(self, db: AsyncSession, email: str, tenant: Tenant) -> Optional[User]:
        cached_user = await self.user_cache.get_user_by_email(email, tenant.tenant_id)
        if cached_user:
            return cached_user

        user = await self.get_by_field(db, "email", email, tenant.tenant_id)
        if user:
            await self.user_cache.cache_user(user, tenant.tenant_id)
        return user


    async def get_users_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[User], int]:
        tenant_id = tenant.tenant_id if tenant else None
        return await self.get_multi(db, page, size, tenant_id)


    async def update_user(self, db: AsyncSession, user_id: UUID, user_data: UserUpdate, tenant: Tenant) -> User:
        # Cache invalidation requires old email if changed
        old_user = await self.get_by_id(db, user_id, tenant.tenant_id)
        old_email = old_user.email if old_user else None

        # Persist update
        updated_user = await self.update(db, user_id, user_data, tenant.tenant_id)

        # Refresh cache
        if old_email:
            await self.user_cache.invalidate_user(user_id, tenant.tenant_id, old_email)
        await self.user_cache.cache_user(updated_user, tenant.tenant_id)

        return updated_user


    async def update_user_password(
        self, db: AsyncSession, user_id: UUID, password_data: UserPasswordUpdate, tenant: Tenant
    ) -> User:
        user = await self.get_user_by_id(db, user_id, tenant)
        if not verify_password(password_data.current_password, user.password):
            raise invalid_credentials()
        user.password = hash_password(password_data.new_password)
        await db.commit()
        await db.refresh(user)

        # Refresh cache
        await self.user_cache.invalidate_user(user_id, tenant.tenant_id, user.email)
        await self.user_cache.cache_user(user, tenant.tenant_id)

        return user


    async def delete_user(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> None:
        # Cache key requires email
        user = await self.get_by_id(db, user_id, tenant.tenant_id)
        user_email = user.email if user else None

        await self.delete(db, user_id, tenant.tenant_id)

        # Invalidate cache entries
        if user_email:
            await self.user_cache.invalidate_user(user_id, tenant.tenant_id, user_email)


    async def verify_user_email(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> User:
        """Mark user email as verified."""
        user = await self.get_user_by_id(db, user_id, tenant)
        user.email_verified_at = func.now()
        await db.commit()
        await db.refresh(user)
        return user


    async def search_users(
        self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[User], int]:
        """Search email/name fields. Returns (users, total_count)."""
        tenant_id = tenant.tenant_id if tenant else None
        return await self.search(db, search_term, page, size, tenant_id)

    async def get_user_roles(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> list[Role]:
        """Get roles assigned to user."""
        user = await self.get_by_id(db, user_id, tenant.tenant_id)
        return user.roles


    async def assign_role_to_user(
        self, db: AsyncSession, user_id: UUID, role_id: UUID, assigned_by: UUID, tenant: Tenant
    ) -> Assignment:
        """Assign role to user."""
        try:
            # Block assignment for deprecated or disabled roles
            role = await db.get(Role, role_id)
            if not role:
                raise ExceptionFactory.not_found("Role", role_id)
            if role.stage in (RoleStage.DEPRECATED, RoleStage.DISABLED):
                raise ExceptionFactory.business_rule(
                    "Role cannot be assigned due to lifecycle stage",
                    {"role_id": str(role_id), "stage": str(role.stage)},
                )
            assignment = Assignment(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
            db.add(assignment)
            await db.commit()
            await db.refresh(assignment)
            return assignment

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e,
                {
                    "operation": "assign_role_to_user",
                    "user_id": user_id,
                    "role_id": role_id,
                },
            )


    async def revoke_role_from_user(self, db: AsyncSession, user_id: UUID, role_id: UUID, tenant: Tenant) -> None:
        """Revoke role from user."""
        query = select(Assignment).where(and_(Assignment.user_id == user_id, Assignment.role_id == role_id))
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise ExceptionFactory.not_found("Assignment", f"user {user_id} role {role_id}")

        await db.delete(assignment)
        await db.commit()


    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> None:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


user_service = UserService()
