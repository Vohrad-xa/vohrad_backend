"""JWT token revocation and blacklisting service."""

from datetime import datetime
from datetime import timezone
from exceptions.jwt_exceptions import TokenRevokedException
from observability.logger import get_logger
from typing import Dict
from typing import Optional
from typing import Set
from uuid import UUID

logger = get_logger(__name__)


class JWTBlacklistService:
    """JWT token blacklisting service with user token tracking."""
    def __init__(self) -> None :
        self._blacklisted_tokens: Set[str] = set()
        self._revocation_cache  : Dict[str, dict] = {}
        self._user_tokens       : Dict[str, Set[str]] = {}  # user_id -> set of jti
        self._token_users       : Dict[str, str] = {}       # jti -> user_id

    def _get_current_utc_time(self) -> datetime:
        """Get current UTC time - centralized utility for consistency."""
        return datetime.now(timezone.utc)

    def _cleanup_empty_user_set(self, user_id: str) -> None:
        """Clean up empty user token sets to prevent memory bloat."""
        if user_id in self._user_tokens and not self._user_tokens[user_id]:
            del self._user_tokens[user_id]

    async def track_user_token(self, user_id: UUID, jti: str) -> None:
        """Track a token for a specific user for bulk operations."""
        user_key = str(user_id)

        # Initialize user's token set if not exists
        if user_key not in self._user_tokens:
            self._user_tokens[user_key] = set()

        # Track token by user and user by token
        self._user_tokens[user_key].add(jti)
        self._token_users[jti] = user_key

    async def revoke_token(self, jti: str, exp: int, reason: str = "manual_revocation") -> bool:
        """Revoke a JWT token by adding it to the blacklist."""
        if await self.is_token_revoked(jti):
            raise TokenRevokedException(f"Token {jti} is already revoked")

        self._blacklisted_tokens.add(jti)
        user_id = self._token_users.get(jti)

        self._revocation_cache[jti] = {
            "revoked_at": self._get_current_utc_time(),
            "expires_at": datetime.fromtimestamp(exp, timezone.utc),
            "reason"    : reason,
            "user_id"   : user_id
        }

        # Remove from user tracking since it's now revoked
        if user_id and user_id in self._user_tokens:
            self._user_tokens[user_id].discard(jti)
            self._cleanup_empty_user_set(user_id)

        # Remove from token->user mapping
        self._token_users.pop(jti, None)

        logger.info(f"Token revoked: {jti}", extra={
            "jti"       : jti,
            "reason"    : reason,
            "expires_at": exp,
            "user_id"   : user_id
        })

        return True

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if a token is revoked/blacklisted."""
        return jti in self._blacklisted_tokens

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from blacklist to prevent memory bloat."""
        now            = self._get_current_utc_time()
        expired_tokens = []

        for jti, metadata in self._revocation_cache.items():
            if now > metadata["expires_at"]:
                expired_tokens.append(jti)

        for jti in expired_tokens:
            # Clean up from all tracking structures
            self._blacklisted_tokens.discard(jti)

            # Remove from user tracking if still exists
            user_id = self._token_users.get(jti)
            if user_id and user_id in self._user_tokens:
                self._user_tokens[user_id].discard(jti)
                self._cleanup_empty_user_set(user_id)

            # Remove from mappings
            self._token_users.pop(jti, None)
            del self._revocation_cache[jti]

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired revoked tokens")

        return len(expired_tokens)

    async def get_revocation_info(self, jti: str) -> Optional[dict]:
        """Get revocation metadata for a token."""
        return self._revocation_cache.get(jti)

    async def revoke_user_tokens(self, user_id: UUID, reason: str = "user_logout") -> int:
        """Revoke all active tokens for a specific user."""
        user_key = str(user_id)

        if user_key not in self._user_tokens:
            logger.info(f"No active tokens found for user {user_id}")
            return 0

        # Get copy of user's tokens to avoid modification during iteration
        user_token_jtis = self._user_tokens[user_key].copy()
        revoked_count = 0

        logger.info(f"Starting bulk revocation for user {user_id}", extra={
            "user_id"    : str(user_id),
            "token_count": len(user_token_jtis),
            "reason"     : reason
        })

        for jti in user_token_jtis:
            try:
                # Check if token is already revoked
                if await self.is_token_revoked(jti):
                    continue

                # Use estimated expiration for bulk operations
                # cleanup_expired_tokens will handle actual expired tokens
                estimated_exp = int(self._get_current_utc_time().timestamp() + 3600)  # 1 hour from now

                # Use existing revoke_token method to maintain consistency
                await self.revoke_token(jti, estimated_exp, reason)
                revoked_count += 1

                logger.debug(f"Revoked token {jti} for user {user_id}", extra={
                    "jti"    : jti,
                    "user_id": str(user_id),
                    "reason" : reason
                })

            except TokenRevokedException:
                # Token was already revoked, skip silently
                continue
            except Exception as e:
                logger.warning(f"Failed to revoke token {jti} for user {user_id}", extra={
                    "jti"    : jti,
                    "user_id": str(user_id),
                    "error"  : str(e)
                })

        logger.info(f"Bulk revocation completed for user {user_id}", extra={
            "user_id"      : str(user_id),
            "revoked_count": revoked_count,
            "reason"       : reason
        })

        return revoked_count


_blacklist_service: Optional[JWTBlacklistService] = None


def get_jwt_blacklist_service() -> JWTBlacklistService:
    """Get JWT blacklist service singleton instance."""
    global _blacklist_service
    if _blacklist_service is None:
        _blacklist_service = JWTBlacklistService()
    return _blacklist_service
