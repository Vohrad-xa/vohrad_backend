"""JWT token revocation and blacklisting service."""

from datetime import datetime
from datetime import timezone
from exceptions.jwt_exceptions import TokenRevokedException
from observability.logger import get_logger
from typing import Optional
from typing import Set
from uuid import UUID

logger = get_logger(__name__)


class JWTBlacklistService:
    """JWT token blacklisting service."""
    def __init__(self) -> None :
        self._blacklisted_tokens: Set[str] = set()
        self._revocation_cache  : dict = {}

    async def revoke_token(self, jti: str, exp: int, reason: str = "manual_revocation") -> bool:
        """Revoke a JWT token by adding it to the blacklist."""
        if await self.is_token_revoked(jti):
            raise TokenRevokedException(f"Token {jti} is already revoked")

        self._blacklisted_tokens.add(jti)
        self._revocation_cache[jti] = {
            "revoked_at": datetime.now(timezone.utc),
            "expires_at": datetime.fromtimestamp(exp, timezone.utc),
            "reason"    : reason
        }

        logger.info(f"Token revoked: {jti}", extra={
            "jti"       : jti,
            "reason"    : reason,
            "expires_at": exp
        })

        return True

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if a token is revoked/blacklisted."""
        return jti in self._blacklisted_tokens

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from blacklist to prevent memory bloat."""
        now            = datetime.now(timezone.utc)
        expired_tokens = []

        for jti, metadata in self._revocation_cache.items():
            if now > metadata["expires_at"]:
                expired_tokens.append(jti)

        for jti in expired_tokens:
            self._blacklisted_tokens.discard(jti)
            del self._revocation_cache[jti]

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired revoked tokens")

        return len(expired_tokens)

    async def get_revocation_info(self, jti: str) -> Optional[dict]:
        """Get revocation metadata for a token."""
        return self._revocation_cache.get(jti)

    async def revoke_user_tokens(self, user_id: UUID, reason: str = "user_logout") -> int:
        """Revoke all tokens for a specific user."""
        # TODO: Implement user token tracking and bulk revocation
        # This would require storing token metadata by user_id
        logger.info(f"Bulk token revocation requested for user {user_id}")
        return 0


_blacklist_service: Optional[JWTBlacklistService] = None


def get_jwt_blacklist_service() -> JWTBlacklistService:
    """Get JWT blacklist service singleton instance."""
    global _blacklist_service
    if _blacklist_service is None:
        _blacklist_service = JWTBlacklistService()
    return _blacklist_service
