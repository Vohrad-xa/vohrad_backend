"""Authorization service with Google Cloud IAM direct policy evaluation."""

from constants.enums import RoleScope
from database import with_default_db, with_tenant_db
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
from uuid import UUID


class AuthorizationService:
    """Google-style authorization with direct policy evaluation and hierarchical precedence."""

    async def _get_tenant_schema(self, tenant_id: UUID) -> str:
        """Resolve tenant schema name via cached resolver (DRY, fast)."""
        from api.tenant import get_tenant_schema_resolver

        resolver = get_tenant_schema_resolver()
        return await resolver.resolve_tenant_schema_by_id(tenant_id)

    async def user_has_role(self, user_id: UUID, role_name: str, tenant_id: Optional[UUID] = None) -> bool:
        """Direct policy check: Does user have this role?"""
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
        """Permission check with hierarchical patterns."""
        permissions = await self._get_user_permissions(user_id, tenant_id)
        permissions = await self._apply_conditional_access(permissions, user_id, tenant_id, resource)

        required_patterns = [
            "*.*",
            f"{resource}.*",
            f"{resource}.{action}"
        ]

        return any(pattern in permissions for pattern in required_patterns)

    async def require_permission(
        self,
        user_id  : UUID,
        resource : str,
        action   : str,
        tenant_id: Optional[UUID] = None
    ) -> None:
        """Require permission or raise authorization exception."""
        if not await self.user_has_permission(user_id, resource, action, tenant_id):
            raise ExceptionFactory.authorization_failed(resource, action)

    async def require_role(self, user_id: UUID, role_name: str, tenant_id: Optional[UUID] = None) -> None:
        """Require role or raise authorization exception."""
        if not await self.user_has_role(user_id, role_name, tenant_id):
            raise ExceptionFactory.authorization_failed("role", role_name)

    async def _apply_conditional_access(
        self,
        permissions: set[str],
        user_id    : UUID,
        tenant_id  : Optional[UUID],
        resource   : str
    ) -> set[str]:
        """Google-style conditional access controls."""
        from datetime import datetime

        current_hour = datetime.now().hour
        if not (9 <= current_hour <= 17):
            permissions = {p for p in permissions if not p.endswith('.delete')}

        if resource:
            permissions = {
                p for p in permissions
                if self._permission_applies_to_resource(p, resource)
            }

        return permissions

    def _permission_applies_to_resource(self, permission: str, resource: str) -> bool:
        """Check if permission applies to the requested resource."""
        if permission == "*.*":
            return True

        perm_resource = permission.split('.')[0]
        return perm_resource == "*" or perm_resource == resource

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
                query = select(Role).join(Assignment).where(
                    Assignment.user_id == user_id,
                    Role.name          == role_name,
                    Role.role_scope    == RoleScope.GLOBAL,
                    Role.is_active
                )

                result = await db.execute(query)
                return result.scalar_one_or_none() is not None

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = "check_global_role",
                details   = {"user_id": str(user_id), "role_name": role_name, "error": str(e)}
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
                query = select(Role).join(Assignment).where(
                    Assignment.user_id == user_id,
                    Role.name          == role_name,
                    Role.role_scope    == RoleScope.TENANT,
                    Role.is_active
                )

                result = await db.execute(query)
                return result.scalar_one_or_none() is not None

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = "check_tenant_role",
                details   = {"user_id": str(user_id), "role_name": role_name, "tenant_id": str(tenant_id), "error": str(e)}
            ) from e

    async def _get_permissions_from_db(
        self,
        user_id   : UUID,
        role_scope: RoleScope,
        tenant_id : Optional[UUID] = None
    ) -> set[str]:
        """Centralized permission retrieval from database."""
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
                query = select(Permission).join(Role).join(Assignment).where(
                    Assignment.user_id == user_id,
                    Role.role_scope    == role_scope,
                    Role.is_active
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
                details   = {"user_id": str(user_id), "role_scope": role_scope.value, "error": str(e)}
            ) from e

        return permissions

    async def _get_user_permissions(self, user_id: UUID, tenant_id: Optional[UUID] = None) -> set[str]:
        """Permission resolution with hierarchical precedence."""
        system_permissions = await self._get_permissions_from_db(user_id, RoleScope.GLOBAL)

        tenant_permissions: set[str] = set()
        if tenant_id:
            tenant_permissions = await self._get_permissions_from_db(user_id, RoleScope.TENANT, tenant_id)

        return self._merge_permissions_with_precedence(tenant_permissions, system_permissions)

    def _merge_permissions_with_precedence(self, tenant_perms: set[str], system_perms: set[str]) -> set[str]:
        """Merge permissions with hierarchical precedence.

        - Tenant roles override system roles
        - Explicit deny permissions (prefixed with '-') take precedence
        - System roles provide baseline access"""
        effective = system_perms.copy()

        for perm in tenant_perms:
            if perm.startswith('-'):
                deny_perm = perm[1:]
                effective.discard(deny_perm)
            else:
                effective.add(perm)

        return effective

    async def _get_roles_from_db(
        self,
        user_id   : UUID,
        role_scope: RoleScope,
        tenant_id : Optional[UUID] = None
    ) -> list[str]:
        """Centralized role retrieval from database."""
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
                query = select(Role).join(Assignment).where(
                    Assignment.user_id == user_id,
                    Role.role_scope == role_scope,
                    Role.is_active
                )

                result       = await db.execute(query)
                role_objects = result.scalars().all()
                roles.extend([role.name for role in role_objects])

        except IntegrityError as e:
            raise constraint_handler.handle_violation(e, context) from e
        except Exception as e:
            raise ExceptionFactory.database_error(
                operation = f"retrieve_{role_scope.value}_roles",
                details   = {"user_id": str(user_id), "role_scope": role_scope.value, "error": str(e)}
            ) from e

        return roles

    async def get_user_roles(self, user_id: UUID, tenant_id: Optional[UUID] = None) -> list[str]:
        """Get list of role names for user."""
        global_roles = await self._get_roles_from_db(user_id, RoleScope.GLOBAL)

        tenant_roles = []
        if tenant_id:
            tenant_roles = await self._get_roles_from_db(user_id, RoleScope.TENANT, tenant_id)

        return global_roles + tenant_roles


authorization_service = AuthorizationService()
