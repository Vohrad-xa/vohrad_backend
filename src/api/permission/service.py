"""
Permission service for role-based access control.

Manages permission CRUD operations, role associations, and access queries
with dynamic constraint handling and efficient batch operations.
"""

from api.common import BaseService
from api.permission.models import Permission
from api.permission.schema import PermissionCreate, PermissionUpdate
from api.role.service import role_service
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from uuid import UUID, uuid4


class PermissionService(BaseService[Permission, PermissionCreate, PermissionUpdate]):
    """Handles permission operations with role-based access control."""

    def __init__(self):
        super().__init__(Permission)

    def get_search_fields(self) -> list[str]:
        """Returns fields available for search operations."""
        return ["resource", "action"]

    async def create_permission(self, db: AsyncSession, permission_data: PermissionCreate) -> Permission:
        """Creates permission with automatic constraint validation."""
        try:
            # Enforce role permissions mutability
            role = await role_service.get_role_by_id(db, permission_data.role_id)
            if not role.permissions_mutable:
                raise ExceptionFactory.business_rule("Permissions are immutable for this role", {
                    "role_id"  : str(role.id),
                    "role_name": role.name,
                })

            # Enforce restricted permission patterns in tenant context
            if (
                (permission_data.resource == "tenant" and permission_data.action in {"create", "update", "delete"})
                or (permission_data.resource == "user" and permission_data.action == "delete")
            ):
                raise ExceptionFactory.authorization_failed("permission", "restricted")

            permission_dict = permission_data.model_dump()
            permission      = Permission(**permission_dict)
            db.add(permission)
            await db.commit()
            await db.refresh(permission)
            return permission

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {
                    "operation": "create_permission",
                    "role_id"  : permission_data.role_id,
                    "resource" : permission_data.resource,
                    "action"   : permission_data.action
                }
            )

    async def get_permission_by_id(self, db: AsyncSession, permission_id: UUID) -> Permission:
        """Retrieves permission by unique identifier."""
        return await self.get_by_id(db, permission_id)

    async def get_permissions_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[Permission], int]:
        """Returns paginated permission list with total count."""
        return await self.get_multi(db, page, size)

    async def update_permission(
        self,
        db             : AsyncSession,
        permission_id  : UUID,
        permission_data: PermissionUpdate,
    ) -> Permission:
        """Updates permission with constraint validation."""
        # Enforce role permissions mutability
        existing = await self.get_by_id(db, permission_id)
        # ETag optimistic concurrency
        update_data = permission_data.model_dump(exclude_unset=True)
        provided_etag = update_data.pop("etag", None)
        if provided_etag is None:
            raise ExceptionFactory.validation_failed("etag", "ETag is required for update")
        if provided_etag != existing.etag:
            raise ExceptionFactory.business_rule("ETag mismatch", {
                "permission_id": str(permission_id),
                "current_etag": existing.etag,
                "provided_etag": provided_etag,
            })

        role = await role_service.get_role_by_id(db, existing.role_id)
        if not role.permissions_mutable:
            raise ExceptionFactory.business_rule("Permissions are immutable for this role", {
                "role_id": str(role.id),
                "role_name": role.name,
            })
        # Enforce restricted patterns
        if (
            (permission_data.resource == "tenant" and permission_data.action in {"create", "update", "delete"})
            or (permission_data.resource == "user" and permission_data.action == "delete")
        ):
            raise ExceptionFactory.authorization_failed("permission", "restricted")

        # Apply updates and refresh ETag
        try:
            for field, value in update_data.items():
                setattr(existing, field, value)
            existing.etag = str(uuid4())[:8]
            await db.commit()
            await db.refresh(existing)
            return existing
        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(e, {"operation": "update_permission", "permission_id": permission_id})

    async def delete_permission(self, db: AsyncSession, permission_id: UUID, etag: str | None = None) -> None:
        """Removes permission from system."""
        # Enforce role permissions mutability
        existing = await self.get_by_id(db, permission_id)
        if etag is None or etag != existing.etag:
            raise ExceptionFactory.business_rule("ETag mismatch", {
                "permission_id": str(permission_id),
                "current_etag": existing.etag,
                "provided_etag": etag,
            })
        from api.role.service import role_service
        role = await role_service.get_role_by_id(db, existing.role_id)
        if not role.permissions_mutable:
            raise ExceptionFactory.business_rule("Permissions are immutable for this role", {
                "role_id": str(role.id),
                "role_name": role.name,
            })

        # Disallow deleting sensitive permissions
        if (
            (existing.resource == "tenant" and existing.action in {"create", "update", "delete"})
            or (existing.resource == "user" and existing.action == "delete")
        ):
            raise ExceptionFactory.authorization_failed("permission", "restricted")
        await self.delete(db, permission_id)

    async def search_permissions(
        self,
        db         : AsyncSession,
        search_term: str,
        page       : int = 1,
        size       : int = 20,
    ) -> tuple[list[Permission], int]:
        """Searches permissions by resource or action with pagination."""
        return await self.search(db, search_term, page, size)

    async def get_role_permissions(self, db: AsyncSession, role_id: UUID) -> list[Permission]:
        """Retrieves all permissions associated with role."""
        from api.role.service import role_service
        role = await role_service.get_role_by_id(db, role_id)
        return role.permissions

    async def get_permissions_for_roles(self, db: AsyncSession, role_ids: list[UUID]) -> list[Permission]:
        """Batch retrieval of permissions for multiple roles."""
        if not role_ids:
            return []
        query  = select(Permission).where(Permission.role_id.in_(role_ids))
        result = await db.execute(query)
        return result.scalars().all()

    async def permission_exists(
        self,
        db      : AsyncSession,
        role_id : UUID,
        resource: str,
        action  : str
        ) -> bool:
        """Validates permission existence for role-resource-action combination."""
        query = select(Permission).where(
            Permission.role_id  == role_id,
            Permission.resource == resource,
            Permission.action   == action
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_permissions_by_resource(self, db: AsyncSession, resource: str) -> list[Permission]:
        """Retrieves permissions filtered by resource type."""
        query  = select(Permission).where(Permission.resource == resource)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_permissions_by_resource_action(
        self, db: AsyncSession, resource: str, action: str
    ) -> list[Permission]:
        """Retrieves permissions by specific resource-action pair."""
        query = select(Permission).where(
            Permission.resource == resource,
            Permission.action   == action
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> None:
        """Processes database constraint violations with dynamic error mapping."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


permission_service = PermissionService()
