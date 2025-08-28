from api.tenant.models import Tenant
from api.user.models import User
from api.user.schema import UserCreate
from api.user.schema import UserPasswordUpdate
from api.user.schema import UserUpdate
from exceptions import duplicate_email
from exceptions import invalid_credentials
from middleware import hash_password
from middleware import verify_password
from services import BaseService
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
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
        """Create new user with email uniqueness check."""
        if await self.exists(db, "email", user_data.email, tenant.tenant_id):
            raise duplicate_email(user_data.email)
        hashed_password = hash_password(user_data.password)
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["password"] = hashed_password
        user_dict["tenant_id"] = tenant.tenant_id

        user = User(**user_dict)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

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
        """Update a user - accepts tenant as parameter"""
        if user_data.email:
            if await self.exists(db, "email", user_data.email, tenant.tenant_id, exclude_id=user_id):
                raise duplicate_email(user_data.email)
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

user_service = UserService()
