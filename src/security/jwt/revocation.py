"""JWT token revocation and blacklisting service."""

from datetime import datetime, timezone
from observability.logger import get_logger
from typing import Optional
from uuid import UUID

logger = get_logger(__name__)


class JWTRevocationService:
    """JWT token revocation service using Claims-Based invalidation."""
    def __init__(self) -> None :
        pass

    def _get_current_utc_time(self) -> datetime:
        """Get current UTC time - centralized utility for consistency."""
        return datetime.now(timezone.utc)

    async def revoke_user_tokens(self, user_id: UUID, reason: str = "user_logout") -> int:
        """Revoke all tokens for a user using Claims-Based revocation."""
        from database.sessions import with_default_db, with_tenant_db
        from sqlalchemy import select, update

        now = self._get_current_utc_time()

        logger.info(f"Starting Claims-Based revocation for user {user_id}", extra={
            "user_id": str(user_id),
            "reason" : reason
        })

        # First check if this is an admin
        from api.admin.models import Admin

        async with with_default_db() as shared_db:
            admin_result = await shared_db.execute(select(Admin).where(Admin.id == user_id))
            admin = admin_result.scalar_one_or_none()

            if admin:
                await shared_db.execute(
                    update(Admin).where(Admin.id == user_id).values(tokens_valid_after=now)
                )
                await shared_db.commit()

                logger.info(f"Claims-Based revocation completed for admin {user_id}", extra={
                    "user_id"      : str(user_id),
                    "revoked_count": 1,
                    "reason"       : reason
                })
                return 1

        # If not admin, search tenant schemas for the user
        from api.tenant.models import Tenant
        from api.user.models import User

        async with with_default_db() as shared_db:
            tenant_result = await shared_db.execute(
                select(Tenant).where(Tenant.status == "active")
            )
            tenants = tenant_result.scalars().all()

        for tenant in tenants:
            async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
                user_result = await tenant_db.execute(select(User).where(User.id == user_id))
                user        = user_result.scalar_one_or_none()

                if user:
                    await tenant_db.execute(
                        update(User).where(User.id == user_id).values(tokens_valid_after=now)
                    )
                    await tenant_db.commit()

                    logger.info(f"Claims-Based revocation completed for user {user_id}", extra={
                        "user_id"      : str(user_id),
                        "tenant_schema": tenant.tenant_schema_name,
                        "revoked_count": 1,
                        "reason"       : reason
                    })
                    return 1

        logger.info(f"User {user_id} not found for revocation", extra={
            "user_id": str(user_id),
            "reason" : reason
        })
        return 0


_jwt_revocation_service: Optional[JWTRevocationService] = None


def get_jwt_revocation_service() -> JWTRevocationService:
    """Get JWT revocation service singleton instance."""
    global _jwt_revocation_service
    if _jwt_revocation_service is None:
        _jwt_revocation_service = JWTRevocationService()
    return _jwt_revocation_service
