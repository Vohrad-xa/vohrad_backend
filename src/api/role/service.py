"""Tenant-scoped role service.

Invariants:
- PREDEFINED/BASIC are immutable.
- Updates/deletes require ETag.
- Reserved role names are blocked.
"""

from .models import Role
from .schema import RoleCreate, RoleUpdate
from api.common import BaseService
from constants import RoleScope, RoleType
from database import constraint_handler
from exceptions import ExceptionFactory
from security.policy import is_reserved_role
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, NoReturn, Optional
from uuid import UUID


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    """Role operations."""

    def __init__(self):
        super().__init__(Role)


    def get_search_fields(self) -> list[str]:
        return ["name", "description"]


    async def create_role(self, db: AsyncSession, role_data: RoleCreate) -> Role:
        try:
            role_dict = role_data.model_dump()
            role = Role(**role_dict)

            if role.role_scope != RoleScope.TENANT:
                raise ExceptionFactory.validation_failed(
                    "role_scope",
                    "Only TENANT scope roles can be created via API"
                )

            role.managed_by = "manager"

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
        return await self.get_by_field(db, "name", name.strip().lower())


    async def get_roles_paginated(
        self,
        db  : AsyncSession,
        page: int = 1,
        size: int = 20
    ) -> tuple[list[Role], int]:
        return await self.get_multi(db, page, size)


    async def update_role(
        self,
        db       : AsyncSession,
        role_id  : UUID,
        role_data: RoleUpdate,
    ) -> Role:
        """Update role with ETag. Raises BaseAppException on immutability, ETag mismatch, or reserved name."""
        role = await self.get_role_by_id(db, role_id)

        if not role.is_mutable:
            raise ExceptionFactory.business_rule(
                "Role is immutable and cannot be modified",
                {
                    "role_id"  : str(role_id),
                    "role_name": role.name,
                },
            )

        update_data = role_data.model_dump(exclude_unset=True)
        provided_etag = update_data.pop("etag", None)

        if provided_etag is None:
            raise ExceptionFactory.validation_failed(
                "etag",
                "ETag is required for update"
            )
        if provided_etag != role.etag:
            raise ExceptionFactory.business_rule(
                "ETag mismatch",
                {
                    "role_id"      : str(role_id),
                    "current_etag" : role.etag,
                    "provided_etag": provided_etag,
                },
            )

        if "name" in update_data:
            new_name = (update_data["name"] or "").strip().lower()
            if is_reserved_role(new_name):
                raise ExceptionFactory.business_rule(
                    "Role name is reserved and cannot be used",
                    {"role_id": str(role_id), "new_name": new_name},
                )


        # Enforce stage changes only for CUSTOM roles
        if "stage" in update_data and role.role_type in (RoleType.BASIC, RoleType.PREDEFINED):
            raise ExceptionFactory.business_rule(
                "Stage can only be changed for CUSTOM roles",
                {"role_id": str(role_id), "role_type": str(role.role_type)},
            )

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
            await self._handle_integrity_error(
                e, {
                    "operation": "update_role",
                    "role_id"  : role_id
                }
            )

    async def delete_role(
        self,
        db     : AsyncSession,
        role_id: UUID,
        etag   : str | None = None
    ) -> None:
        """Delete role with ETag. Raises BaseAppException on immutability or ETag mismatch."""
        role = await self.get_role_by_id(db, role_id)
        if not role.is_mutable:
            raise ExceptionFactory.business_rule(
                "Immutable role cannot be deleted",
                {
                    "role_id"  : str(role_id),
                    "role_name": role.name,
                },
            )
        if etag is None or etag != role.etag:
            raise ExceptionFactory.business_rule(
                "ETag mismatch",
                {
                    "role_id"      : str(role_id),
                    "current_etag" : role.etag,
                    "provided_etag": etag,
                },
            )

        await self.delete(db, role_id)


    async def search_roles(
        self,
        db         : AsyncSession,
        search_term: str,
        page       : int = 1,
        size       : int = 20,
    ) -> tuple[list[Role], int]:
        return await self.search(db, search_term, page, size)


    async def get_active_roles(self, db: AsyncSession) -> list[Role]:
        filters = Role.is_active
        roles, _ = await self.get_filtered(db, filters, page=1, size=1000)
        return roles


    async def activate_role(self, db: AsyncSession, role_id: UUID) -> Role:
        role = await self.get_role_by_id(db, role_id)
        role.is_active = True
        await db.commit()
        await db.refresh(role)
        return role


    async def deactivate_role(self, db: AsyncSession, role_id: UUID) -> Role:
        role = await self.get_role_by_id(db, role_id)
        role.is_active = False
        await db.commit()
        await db.refresh(role)
        return role


    async def _handle_integrity_error(
        self,
        error            : IntegrityError,
        operation_context: dict[str, Any]
    ) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


role_service = RoleService()
