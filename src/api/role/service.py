"""Role service following enterprise patterns with multi-tenant support."""

from api.role.models import Role
from api.role.schema import RoleCreate
from api.role.schema import RoleUpdate
from exceptions import duplicate_role_name
from services import BaseService
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from typing import Optional
from uuid import UUID


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    """Service class for role business logic"""

    def __init__(self):
        super().__init__(Role)

    def get_search_fields(self) -> list[str]:
        """Return searchable fields for role."""
        return ["name", "description"]

    async def create_role(self, db: AsyncSession, role_data: RoleCreate) -> Role:
        """Create new role - tenant context handled by database schema routing."""
        try:
            role_dict = role_data.model_dump()
            role = Role(**role_dict)
            db.add(role)
            await db.commit()
            await db.refresh(role)
            return role

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {"operation": "create_role", "name": role_data.name})

    async def get_role_by_id(self, db: AsyncSession, role_id: UUID) -> Role:
        """Get role by ID."""
        return await self.get_by_id(db, role_id)

    async def get_role_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """Get role by name."""
        return await self.get_by_field(db, "name", name.strip().lower())

    async def get_roles_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[Role], int]:
        """Get paginated list of roles"""
        return await self.get_multi(db, page, size)

    async def update_role(
        self,
        db       : AsyncSession,
        role_id  : UUID,
        role_data: RoleUpdate,
     ) -> Role:
        """Update role - enterprise pattern with inherited constraint protection."""
        return await self.update(db, role_id, role_data)

    async def delete_role(self, db: AsyncSession, role_id: UUID) -> None:
        """Delete role"""
        await self.delete(db, role_id)

    async def search_roles(
        self,
        db         : AsyncSession,
        search_term: str,
        page       : int = 1,
        size       : int = 20,
    ) -> tuple[list[Role], int]:
        """Search roles using the generic search method."""
        return await self.search(db, search_term, page, size)

    async def get_active_roles(self, db: AsyncSession) -> list[Role]:
        """Get all active roles"""
        filters = Role.is_active
        roles, _ = await self.get_filtered(db, filters, page=1, size=1000)
        return roles

    async def activate_role(self, db: AsyncSession, role_id: UUID) -> Role:
        """Mark role as active"""
        role           = await self.get_role_by_id(db, role_id)
        role.is_active = True
        await db.commit()
        await db.refresh(role)
        return role

    async def deactivate_role(self, db: AsyncSession, role_id: UUID) -> Role:
        """Mark role as inactive"""
        role           = await self.get_role_by_id(db, role_id)
        role.is_active = False
        await db.commit()
        await db.refresh(role)
        return role

    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any],) -> None:
        """Handle role-specific constraint violations - enterprise pattern."""
        constraint_name = self._extract_constraint_name(error)

        if constraint_name == "idx_roles_name" or "name" in str(error):
            role_name = operation_context.get("name") or "unknown"
            raise duplicate_role_name(role_name)

        raise error


role_service = RoleService()
