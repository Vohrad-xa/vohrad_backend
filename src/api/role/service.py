"""Role business logic service with multi-tenant isolation."""

from api.common import BaseService
from api.role.models import Role
from api.role.schema import RoleCreate, RoleUpdate
from constants.enums import RoleType
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
from uuid import UUID


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):

    def __init__(self):
        super().__init__(Role)

    def get_search_fields(self) -> list[str]:
        """Return searchable fields for role."""
        return ["name", "description"]

    async def create_role(self, db: AsyncSession, role_data: RoleCreate) -> Role:
        """Create role with constraint validation."""
        try:
            role_dict = role_data.model_dump()
            role = Role(**role_dict)
            # Tenant API supports tenant-scoped roles only
            from constants.enums import RoleScope
            if role.role_scope != RoleScope.TENANT:
                raise ExceptionFactory.validation_failed("role_scope", "Only TENANT scope roles can be created via API")
            # Enable full mutability for CUSTOM roles
            if str(role.role_type) in (RoleType.CUSTOM.value, str(RoleType.CUSTOM)) or role.role_type == RoleType.CUSTOM:
                role.is_mutable = True
                role.permissions_mutable = True
                role.is_deletable = True
            db.add(role)
            await db.commit()
            await db.refresh(role)
            return role

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {"operation": "create_role", "name": role_data.name})

    async def get_role_by_id(self, db: AsyncSession, role_id: UUID) -> Role:
        return await self.get_by_id(db, role_id)

    async def get_role_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """Case-insensitive lookup."""
        return await self.get_by_field(db, "name", name.strip().lower())

    async def get_roles_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[Role], int]:
        """Returns (roles, total_count)."""
        return await self.get_multi(db, page, size)

    async def update_role(
        self,
        db       : AsyncSession,
        role_id  : UUID,
        role_data: RoleUpdate,
     ) -> Role:
        """Updating role with constraint protection."""
        # Enforce immutability for BASIC/PREDEFINED (is_mutable == False)
        role = await self.get_role_by_id(db, role_id)
        if not role.is_mutable:
            raise ExceptionFactory.business_rule("Role is immutable and cannot be modified", {
                "role_id": str(role_id),
                "role_name": role.name,
            })

        # Enforce reserved name protection on rename
        update_data = role_data.model_dump(exclude_unset=True)
        # Require ETag for optimistic concurrency control
        provided_etag = update_data.pop("etag", None)
        if provided_etag is None:
            raise ExceptionFactory.validation_failed("etag", "ETag is required for update")
        if provided_etag != role.etag:
            raise ExceptionFactory.business_rule("ETag mismatch", {
                "role_id": str(role_id),
                "current_etag": role.etag,
                "provided_etag": provided_etag,
            })

        if "name" in update_data:
            new_name = (update_data["name"] or "").strip().lower()
            reserved = {"admin", "super_admin", "manager", "employee", "user", "viewer"}
            if new_name in reserved:
                raise ExceptionFactory.business_rule("Role name is reserved and cannot be used", {
                    "role_id": str(role_id),
                    "new_name": new_name,
                })

        # Apply updates and refresh ETag for CUSTOM roles
        try:
            for field, value in update_data.items():
                setattr(role, field, value)

            if role.role_type == RoleType.CUSTOM:
                role.update_etag()

            await db.commit()
            await db.refresh(role)
            return role
        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {"operation": "update_role", "role_id": role_id})

    async def delete_role(self, db: AsyncSession, role_id: UUID, etag: str | None = None) -> None:
        """Delete role with immutability and ETag optimistic concurrency checks."""
        role = await self.get_role_by_id(db, role_id)
        if not role.is_mutable:
            raise ExceptionFactory.business_rule("Role is immutable and cannot be deleted", {
                "role_id": str(role_id),
                "role_name": role.name,
            })
        if etag is None or etag != role.etag:
            raise ExceptionFactory.business_rule("ETag mismatch", {
                "role_id": str(role_id),
                "current_etag": role.etag,
                "provided_etag": etag,
            })

        await self.delete(db, role_id)

    async def search_roles(
        self,
        db         : AsyncSession,
        search_term: str,
        page       : int = 1,
        size       : int = 20,
    ) -> tuple[list[Role], int]:
        """Search name/description. Returns (roles, total_count)."""
        return await self.search(db, search_term, page, size)

    async def get_active_roles(self, db: AsyncSession) -> list[Role]:
        filters = Role.is_active
        roles, _ = await self.get_filtered(db, filters, page=1, size=1000)
        return roles

    async def activate_role(self, db: AsyncSession, role_id: UUID) -> Role:
        role           = await self.get_role_by_id(db, role_id)
        role.is_active = True
        await db.commit()
        await db.refresh(role)
        return role

    async def deactivate_role(self, db: AsyncSession, role_id: UUID) -> Role:
        role           = await self.get_role_by_id(db, role_id)
        role.is_active = False
        await db.commit()
        await db.refresh(role)
        return role

    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> None:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


role_service = RoleService()
