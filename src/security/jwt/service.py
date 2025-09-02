"""JWT service for authentication module following modular architecture."""

from typing import TYPE_CHECKING
from typing import Optional
from uuid import UUID

if TYPE_CHECKING:
    from api.user.models import User

from .revocation import get_jwt_blacklist_service
from database.sessions import with_default_db
from database.sessions import with_tenant_db
from exceptions.application import AuthenticationException
from exceptions.jwt_exceptions import TokenInvalidException
from security.jwt.engine import JWTEngine
from security.jwt.tokens import AccessToken
from security.jwt.tokens import AuthenticatedUser
from security.jwt.tokens import RefreshToken
from security.jwt.tokens import TokenPair
from security.jwt.tokens import create_admin_access_payload
from security.jwt.tokens import create_refresh_payload
from security.jwt.tokens import create_user_access_payload
from security.password import verify_password
from services.tenant_service import get_tenant_schema_service


class AuthJWTService:
    """JWT service for authentication operations."""
    def __init__(self):
        self.jwt_engine            = JWTEngine()
        self.blacklist_service     = get_jwt_blacklist_service()
        self.tenant_schema_service = get_tenant_schema_service()

    async def authenticate_user(
        self,
      email    : str,
      password : str,
      tenant_id: UUID
    ) -> tuple :
        """Authenticate tenant user using proper service patterns."""
        # Lazy imports to avoid circular dependencies
        from api.tenant.service import TenantService
        from api.user.service import UserService

        tenant_service = TenantService()
        user_service   = UserService()

        # Get tenant from shared schema using proper service layer
        async with with_default_db() as shared_db:
            tenant = await tenant_service.get_by_id(shared_db, tenant_id)
            if not tenant:
                raise AuthenticationException("Invalid tenant")

        # Then get user from tenant schema using proper session management
        async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
            user = await user_service.get_user_by_email(tenant_db, email, tenant)

            if not user or not verify_password(password, user.password):
                raise AuthenticationException("Invalid credentials")

            return user, tenant

    async def authenticate_admin(
        self,
    email   : str,
    password: str
    ):
        """Authenticate global admin using proper SQLAlchemy patterns."""
        from api.admin.models import Admin
        from sqlalchemy import select

        async with with_default_db() as shared_db:
            result = await shared_db.execute(
                select(Admin).where(
                    Admin.email     == email,
                    Admin.is_active,
                )
            )
            admin = result.scalar_one_or_none()

            if not admin or not verify_password(password, admin.password):
                raise AuthenticationException("Invalid admin credentials")

            return admin

    async def create_user_tokens(self, user: "User") -> TokenPair:
        """Create tokens for user."""
        access_payload = create_user_access_payload(
            user_id   = user.id,
            email     = user.email,
            tenant_id = user.tenant_id
        )

        access_token_str = self.jwt_engine.encode_token(access_payload)
        access_expires   = self.jwt_engine.create_expiry()

        access_token = AccessToken(
            token      = access_token_str,
            payload    = access_payload,
            expires_at = access_expires
        )

        refresh_payload = create_refresh_payload(
            user_id   = user.id,
            tenant_id = user.tenant_id,
            user_type = "user"
        )

        refresh_token_str = self.jwt_engine.encode_token(refresh_payload)
        refresh_expires   = self.jwt_engine.create_expiry(days=7)

        refresh_token = RefreshToken(
            token      = refresh_token_str,
            payload    = refresh_payload,
            expires_at = refresh_expires
        )

        # Track tokens for bulk revocation capabilities
        await self.blacklist_service.track_user_token(user.id, access_payload["jti"])
        await self.blacklist_service.track_user_token(user.id, refresh_payload["jti"])

        return TokenPair(
            access_token  = access_token,
            refresh_token = refresh_token
        )

    async def create_admin_tokens(self, admin) -> TokenPair:
        """Create tokens for admin."""
        access_payload = create_admin_access_payload(
            admin_id = admin.id,
            email    = admin.email
        )

        access_token_str = self.jwt_engine.encode_token(access_payload)
        access_expires   = self.jwt_engine.create_expiry()

        access_token = AccessToken(
            token      = access_token_str,
            payload    = access_payload,
            expires_at = access_expires
        )

        refresh_payload = create_refresh_payload(
            user_id   = admin.id,
            tenant_id = None,
            user_type = "admin"
        )

        refresh_token_str = self.jwt_engine.encode_token(refresh_payload)
        refresh_expires   = self.jwt_engine.create_expiry(days=7)

        refresh_token = RefreshToken(
            token      = refresh_token_str,
            payload    = refresh_payload,
            expires_at = refresh_expires
        )

        # Track tokens for bulk revocation capabilities
        await self.blacklist_service.track_user_token(admin.id, access_payload["jti"])
        await self.blacklist_service.track_user_token(admin.id, refresh_payload["jti"])

        return TokenPair(
            access_token  = access_token,
            refresh_token = refresh_token
        )

    async def validate_access_token(self, token: str, request_subdomain: Optional[str] = None) -> AuthenticatedUser:
        """Validate token and return user context with enterprise tenant-subdomain validation."""
        payload = self.jwt_engine.decode_token(token)

        if payload.get("token_type") != "access":
            raise TokenInvalidException("Invalid token type")

        # Check if token is revoked
        jti = payload.get("jti")
        if jti and await self.blacklist_service.is_token_revoked(jti):
            raise TokenInvalidException("Token has been revoked")

        # Enterprise security: Always validate tenant-subdomain match for tenant users
        jwt_tenant_id = payload.get("tenant_id")
        user_type = payload.get("user_type")

        if user_type == "user" and jwt_tenant_id and request_subdomain:
            try:
                # Resolve tenant schema from subdomain
                actual_tenant_schema = await self.tenant_schema_service.resolve_tenant_schema(request_subdomain)

                # Get tenant details from JWT tenant_id for validation
                from api.tenant.service import TenantService
                tenant_service = TenantService()

                async with with_default_db() as shared_db:
                    jwt_tenant = await tenant_service.get_by_id(shared_db, UUID(jwt_tenant_id))
                    if not jwt_tenant:
                        raise TokenInvalidException("Token references invalid tenant")

                    # Critical security check: validate schema names match
                    if jwt_tenant.tenant_schema_name != actual_tenant_schema:
                        raise TokenInvalidException(
                            f"Security violation: JWT tenant '{jwt_tenant.tenant_schema_name}' "
                            f"does not match request subdomain '{request_subdomain}'"
                        )

            except TokenInvalidException:
                raise
            except Exception as e:
                raise TokenInvalidException(f"Tenant validation failed: {e!s}") from e

        return AuthenticatedUser(
            user_id   = UUID(payload["sub"]),
            email     = payload["email"],
            tenant_id = UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
            user_type = payload["user_type"]
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token."""
        payload = self.jwt_engine.decode_token(refresh_token)

        if payload.get("token_type") != "refresh":
            raise TokenInvalidException("Invalid refresh token type")

        user_id   = UUID(payload["sub"])
        user_type = payload["user_type"]
        tenant_id = UUID(payload["tenant_id"]) if payload.get("tenant_id") else None

        if user_type == "user" and tenant_id:
            # Lazy imports to avoid circular dependencies
            from api.tenant.service import TenantService
            from api.user.service import UserService

            tenant_service = TenantService()
            user_service   = UserService()

            # Get tenant using service layer
            async with with_default_db() as shared_db:
                tenant = await tenant_service.get_by_id(shared_db, tenant_id)
                if not tenant:
                    raise TokenInvalidException("Tenant not found")

            # Get user with proper tenant context
            async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
                user = await user_service.get_user_by_id(tenant_db, user_id, tenant)
                if not user:
                    raise TokenInvalidException("User not found")
                return await self.create_user_tokens(user)

        elif user_type == "admin":
            from api.admin.models import Admin
            from sqlalchemy import select

            async with with_default_db() as shared_db:
                result = await shared_db.execute(
                    select(Admin).where(
                        Admin.id        == user_id,
                        Admin.is_active,
                    )
                )
                admin = result.scalar_one_or_none()

                if not admin:
                    raise TokenInvalidException("Admin not found")
                return await self.create_admin_tokens(admin)

        else:
            raise TokenInvalidException("Invalid token context")

    async def login_user(self, login_request, tenant=None) -> TokenPair:
        """Complete user login flow with optional tenant object."""
        if tenant         :
            effective_tenant_id = tenant.tenant_id
        else:
            effective_tenant_id = login_request.tenant_id

        user, _tenant = await self.authenticate_user(
            login_request.email,
            login_request.password,
            effective_tenant_id
        )
        return await self.create_user_tokens(user)

    async def login_admin(self, login_request) -> TokenPair:
        """Complete admin login flow."""
        admin = await self.authenticate_admin(
            login_request.email,
            login_request.password
        )
        return await self.create_admin_tokens(admin)

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Alias for refresh_access_token to match router expectations."""
        return await self.refresh_access_token(refresh_token)

    async def logout_user(self, access_token: str) -> bool:
        """Logout user by revoking their token."""
        try:
            payload = self.jwt_engine.decode_token(access_token)
            jti     = payload.get("jti")
            exp     = payload.get("exp")

            if jti and exp:
                return await self.blacklist_service.revoke_token(jti, exp, "user_logout")
            return False
        except Exception:
            return True

    async def logout_user_from_all_devices(self, user_id: UUID, reason: str = "logout_all_devices") -> int:
        """Logout user from all devices by revoking all their tokens."""
        return await self.blacklist_service.revoke_user_tokens(user_id, reason)


_auth_jwt_service: Optional[AuthJWTService] = None


def get_auth_jwt_service() -> AuthJWTService:
    """Get auth JWT service singleton instance."""
    global _auth_jwt_service
    if _auth_jwt_service is None:
        _auth_jwt_service = AuthJWTService()
    return _auth_jwt_service
