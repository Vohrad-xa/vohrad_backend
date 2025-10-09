"""Authorization service (direct policy evaluation).

Principles:
- Tenant overrides global.
- Wildcards supported (e.g., "*.*").
- Optional conditional filters may restrict actions.
"""

from ..policy import apply_conditional_access, merge_permissions_with_precedence
from api.tenant import get_tenant_schema_resolver
from constants import RoleScope, RoleStage
from database import constraint_handler, with_default_db, with_tenant_db
from datetime import datetime, timezone
from exceptions import ExceptionFactory
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo


class AuthorizationService:
    """Authorization with hierarchical precedence."""

    async def _get_tenant_schema(self, tenant_id: UUID) -> str:
        """Resolve tenant schema name via cached resolver (DRY, fast)."""
        resolver = get_tenant_schema_resolver()
        return await resolver.resolve_tenant_schema_by_id(tenant_id)


    async def user_has_role(
        self,
        user_id  : UUID,
        role_name: str,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """Return True if user has role."""
        if await self._has_global_role(user_id, role_name):
            return True

        if tenant_id:
            return await self._has_tenant_role(user_id, role_name, tenant_id)

        return False


    async def user_has_permission(
        self,
        user_id  : UUID,
        resource : str,
        action   : str,
        tenant_id: Optional[UUID] = None
    ) -> bool:
        """Return True if user has permission."""
        permissions = await self._get_user_permissions(user_id, tenant_id)
        # Apply conditional access using tenant-aware timezone and working hours
        current_minute, bh_start, bh_end = await self._get_time_policy_params(tenant_id)
        permissions = apply_conditional_access(
            permissions,
            resource,
            current_hour        = current_minute,
            business_hour_start = bh_start,
            business_hour_end   = bh_end,
        )

        required_patterns = ["*.*", f"{resource}.*", f"{resource}.{action}"]

        return any(pattern in permissions for pattern in required_patterns)


    async def _get_time_policy_params(self, tenant_id: Optional[UUID]) -> tuple[int, int | None, int | None]:
        """Return current minute-of-day in tenant TZ and tenant-specific business hours (minutes).

        Fallbacks:
        - Timezone: UTC if missing/invalid.
        - Business hours: (None, None) if not set (policy will use SecurityDefaults, in hours, converted to minutes).
        """
        tz_name : Optional[str] = None
        bh_start: int | None = None
        bh_end  : int | None = None
        if tenant_id:
            try:
                from api.tenant.service import tenant_service
                async with with_default_db() as shared_db:
                    tenant   = await tenant_service.get_tenant_by_id(shared_db, tenant_id)
                    tz_name  = getattr(tenant, "timezone", None)
                    bh_start = getattr(tenant, "business_hour_start", None)
                    bh_end   = getattr(tenant, "business_hour_end", None)
            except Exception:
                tz_name  = None
                bh_start = None
                bh_end   = None

        try:
            tzinfo = ZoneInfo(tz_name) if tz_name else timezone.utc
        except Exception:
            tzinfo = timezone.utc

        now = datetime.now(tzinfo)
        current_minute = now.hour * 60 + now.minute

        # Values <= 23 are treated as hours; 0..1439 treated as minutes
        def normalize(v: Optional[int]) -> Optional[int]:
            if v is None:
                return None
            if 0 <= v <= 23:
                return v * 60
            if 0 <= v <= 1439:
                return v
            return None

        return current_minute, normalize(bh_start), normalize(bh_end)


    async def require_permission(
        self,
        user_id  : UUID,
        resource : str,
        action   : str,
        tenant_id: Optional[UUID] = None
    ) -> None:
        """Require permission or raise."""
        if not await self.user_has_permission(user_id, resource, action, tenant_id):
            raise ExceptionFactory.authorization_failed(resource, action)


    async def require_role(
        self,
        user_id  : UUID,
        role_name: str,
        tenant_id: Optional[UUID] = None
    ) -> None:
        """Require role or raise."""
        if not await self.user_has_role(user_id, role_name, tenant_id):
            raise ExceptionFactory.authorization_failed("role", role_name)


    async def _has_global_role(self, user_id: UUID, role_name: str) -> bool:
        """Check if user has global role in shared schema."""
        context = {
            "operation": "global_role_check",
            "user_id"  : user_id,
            "role_name": role_name
        }

        try:
            from api.assignment.models import Assignment
            from api.role.models import Role

            async with with_default_db() as db:
                query = (
                    select(Role)
                    .join(Assignment)
                    .where(
                        Assignment.user_id == user_id,
                        Role.name          == role_name,
                        Role.role_scope    == RoleScope.GLOBAL,
                        Role.is_active,
                        Role.stage != RoleStage.DISABLED,
                    )
                )

                result = await db.execute(query)
                return result.scalar_one_or_none() is not None

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = "check_global_role",
                details   = {
                    "user_id"  : str(user_id),
                    "role_name": role_name,
                    "error"    : str(e)
                }
            ) from e


    async def _has_tenant_role(self, user_id: UUID, role_name: str, tenant_id: UUID) -> bool:
        """Check if user has tenant role in the correct tenant schema (resolved from tenant_id)."""
        context = {
            "operation": "tenant_role_check",
            "user_id"  : user_id,
            "role_name": role_name,
            "tenant_id": tenant_id
        }

        try:
            from api.assignment.models import Assignment
            from api.role.models import Role

            tenant_schema = await self._get_tenant_schema(tenant_id)
            async with with_tenant_db(tenant_schema) as db:
                query = (
                    select(Role)
                    .join(Assignment)
                    .where(
                        Assignment.user_id == user_id,
                        Role.name          == role_name,
                        Role.role_scope    == RoleScope.TENANT,
                        Role.is_active,
                        Role.stage != RoleStage.DISABLED,
                    )
                )

                result = await db.execute(query)
                return result.scalar_one_or_none() is not None

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = "check_tenant_role",
                details   = {
                    "user_id"  : str(user_id),
                    "role_name": role_name,
                    "tenant_id": str(tenant_id),
                    "error"    : str(e)
                },
            ) from e


    async def _get_permissions_from_db(
        self,
        user_id   : UUID,
        role_scope: RoleScope,
        tenant_id : Optional[UUID] = None
    ) -> set[str]:
        """Retrieve permissions from database."""
        permissions: set[str] = set()
        context = {
            "operation" : f"{role_scope.value}_permissions_query",
            "user_id"   : user_id,
            "role_scope": role_scope.value
        }

        if tenant_id:
            context["tenant_id"] = tenant_id

        try:
            from api.assignment.models import Assignment
            from api.permission.models import Permission
            from api.role.models import Role

            if role_scope == RoleScope.TENANT:
                if tenant_id is None:
                    return permissions
                tenant_schema = await self._get_tenant_schema(tenant_id)
                db_ctx = with_tenant_db(tenant_schema)
            else:
                db_ctx = with_default_db()

            async with db_ctx as db:
                query = (
                    select(Permission)
                    .join(Role)
                    .join(Assignment)
                    .where(
                        Assignment.user_id == user_id,
                        Role.role_scope == role_scope,
                        Role.is_active,
                        Role.stage != RoleStage.DISABLED,
                    )
                )

                result = await db.execute(query)
                perms = result.scalars().all()

                for perm in perms:
                    permissions.add(f"{perm.resource}.{perm.action}")

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = f"retrieve_{role_scope.value}_permissions",
                details   = {
                    "user_id"   : str(user_id),
                    "role_scope": role_scope.value,
                    "error"     : str(e)
                },
            ) from e

        return permissions


    async def _get_user_permissions(self, user_id: UUID, tenant_id: Optional[UUID] = None) -> set[str]:
        """Resolve permissions with precedence."""
        system_permissions = await self._get_permissions_from_db(user_id, RoleScope.GLOBAL)

        tenant_permissions: set[str] = set()
        if tenant_id:
            tenant_permissions = await self._get_permissions_from_db(user_id, RoleScope.TENANT, tenant_id)

        return merge_permissions_with_precedence(tenant_permissions, system_permissions)


    async def _get_roles_from_db(
        self,
        user_id   : UUID,
        role_scope: RoleScope,
        tenant_id : Optional[UUID] = None
    ) -> list[str]:
        """Retrieve roles from database."""
        roles: list[str] = []
        context = {
            "operation" : f"{role_scope.value}_roles_query",
            "user_id"   : user_id,
            "role_scope": role_scope.value
        }

        if tenant_id:
            context["tenant_id"] = tenant_id

        try:
            from api.assignment.models import Assignment
            from api.role.models import Role

            if role_scope == RoleScope.TENANT:
                if tenant_id is None:
                    return roles
                tenant_schema = await self._get_tenant_schema(tenant_id)
                db_ctx = with_tenant_db(tenant_schema)
            else:
                db_ctx = with_default_db()

            async with db_ctx as db:
                query = (
                    select(Role)
                    .join(Assignment)
                    .where(Assignment.user_id == user_id, Role.role_scope == role_scope, Role.is_active)
                )

                result = await db.execute(query)
                role_objects = result.scalars().all()
                roles.extend([role.name for role in role_objects])

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = f"retrieve_{role_scope.value}_roles",
                details   = {
                    "user_id"   : str(user_id),
                    "role_scope": role_scope.value,
                    "error"     : str(e)
                },
            ) from e

        return roles


    async def get_user_roles(
        self,
        user_id  : UUID,
        tenant_id: Optional[UUID] = None
    ) -> list[str]:
        """Return role names for user."""
        global_roles = await self._get_roles_from_db(user_id, RoleScope.GLOBAL)

        tenant_roles = []
        if tenant_id:
            tenant_roles = await self._get_roles_from_db(user_id, RoleScope.TENANT, tenant_id)

        return global_roles + tenant_roles


authorization_service = AuthorizationService()
