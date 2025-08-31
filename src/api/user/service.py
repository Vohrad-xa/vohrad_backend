from api.assignment.models import Assignment
from api.role.models import Role
from api.tenant.models import Tenant
from api.user.models import User
from api.user.schema import UserCreate
from api.user.schema import UserPasswordUpdate
from api.user.schema import UserUpdate
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory
from exceptions import invalid_credentials
from middleware import hash_password
from middleware import verify_password
from services import BaseService
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from typing import Optional
from uuid import UUID


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """Service class for user business logic"""

    def __init__(self):
        super().__init__(User)

    def get_search_fields(self) -> list[str]:
        """Return searchable fields for user."""
        return ["email", "first_name", "last_name", "city"]

    async def create_user(self, db: AsyncSession, user_data: UserCreate, tenant: Tenant) -> User:
        """Create new user - enterprise pattern with database-first approach."""
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
        """Get user by ID."""
        return await self.get_by_id(db, user_id, tenant.tenant_id)

    async def get_user_by_email(self, db: AsyncSession, email: str, tenant: Tenant) -> Optional[User]:
        """Get user by email."""
        return await self.get_by_field(db, "email", email, tenant.tenant_id)

    async def get_users_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[User], int]:
        """Get paginated list of users"""
        tenant_id = tenant.tenant_id if tenant else None
        return await self.get_multi(db, page, size, tenant_id)

    async def update_user(self, db: AsyncSession, user_id: UUID, user_data: UserUpdate, tenant: Tenant) -> User:
        """Update user - enterprise pattern with inherited constraint protection."""
        return await self.update(db, user_id, user_data, tenant.tenant_id)

    async def update_user_password(
        self, db: AsyncSession, user_id: UUID, password_data: UserPasswordUpdate, tenant: Tenant
    ) -> User:
        """Update user password with current password verification"""
        user = await self.get_user_by_id(db, user_id, tenant)
        if not verify_password(password_data.current_password, user.password):
            raise invalid_credentials()
        user.password = hash_password(password_data.new_password)
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> None:
        """Delete user - accepts tenant as parameter"""
        await self.delete(db, user_id, tenant.tenant_id)

    async def verify_user_email(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> User:
        """Mark user email as verified"""
        user = await self.get_user_by_id(db, user_id, tenant)
        user.email_verified_at = func.now()
        await db.commit()
        await db.refresh(user)
        return user

    async def search_users(
        self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[User], int]:
        """Search users using the generic search method."""
        tenant_id = tenant.tenant_id if tenant else None
        return await self.search(db, search_term, page, size, tenant_id)

    async def get_user_roles(self, db: AsyncSession, user_id: UUID, tenant: Tenant) -> list[Role]:
        """Get all roles assigned to user."""
        user = await self.get_by_id(db, user_id, tenant.tenant_id)
        # Clean, enterprise-grade: use ORM relationships
        return user.roles

    async def assign_role_to_user(
        self, db: AsyncSession, user_id: UUID, role_id: UUID, assigned_by: UUID, tenant: Tenant
    ) -> Assignment:
        """Assign role to user with proper constraint handling."""
        try:
            assignment = Assignment(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by
            )
            db.add(assignment)
            await db.commit()
            await db.refresh(assignment)
            return assignment

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {
                    "operation": "assign_role_to_user",
                    "user_id": user_id,
                    "role_id": role_id,
                }
            )

    async def revoke_role_from_user(self, db: AsyncSession, user_id: UUID, role_id: UUID, tenant: Tenant) -> None:
        """Revoke role from user - follows established deletion patterns."""
        query = select(Assignment).where(
            and_(Assignment.user_id == user_id, Assignment.role_id == role_id)
        )
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise ExceptionFactory.not_found("Assignment", f"user {user_id} role {role_id}")

        await db.delete(assignment)
        await db.commit()

    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> None:
        """Enterprise-grade constraint handling - centralized, modular, DRY."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


user_service = UserService()
