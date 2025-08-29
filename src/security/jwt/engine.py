"""Pure JWT token operations following enterprise security standards."""

import jwt
from config.jwt import get_jwt_config
from config.keys import get_key_manager
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from exceptions.jwt_exceptions import TokenExpiredException
from exceptions.jwt_exceptions import TokenInvalidException
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union
from uuid import uuid4


class JWTEngine:
    """Pure JWT operations with zero business logic coupling."""
    def __init__(self):
        self.jwt_config  = get_jwt_config()
        self.key_manager = get_key_manager()

    @property
    def _signing_key(self) -> Union[str, bytes]:
        """Get JWT signing key (private key for RS256)."""
        return self.key_manager.jwt_secret_key

    @property
    def _verify_key(self) -> Union[str, bytes]:
        """Get JWT verification key (public key for RS256)."""
        return self.key_manager.jwt_verify_key

    @property
    def _algorithm(self) -> str:
        """Get JWT signing algorithm."""
        return self.key_manager.jwt_algorithm

    @property
    def _issuer(self) -> str:
        """Get JWT issuer."""
        return self.jwt_config.issuer

    @property
    def _audience(self) -> str:
        """Get JWT audience."""
        return self.jwt_config.audience

    def encode_token(self, payload: Dict[str, Any]) -> str:
        """Encode JWT token with enterprise security standards."""
        now = datetime.now(timezone.utc)

        # Add standard claims following RFC 7519
        standard_payload = {
            **payload,
            "iss": self._issuer,         # Issuer
            "aud": self._audience,       # Audience
            "iat": int(now.timestamp()),  # Issued at
            "nbf": int(now.timestamp()),  # Not before
            "jti": str(uuid4()),         # JWT ID for tracking
        }

        return jwt.encode(
            standard_payload,
            self._signing_key,
            algorithm = self._algorithm
        )

    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """Decode and validate JWT token."""
        try:
            options = {"verify_exp": verify_exp}

            payload = jwt.decode(
                token,
                self._verify_key,
                algorithms = [self._algorithm],
                audience   = self._audience,
                issuer     = self._issuer,
                options    = options
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Token has expired") from None
        except jwt.InvalidAudienceError:
            raise TokenInvalidException("Invalid token audience") from None
        except jwt.InvalidIssuerError:
            raise TokenInvalidException("Invalid token issuer") from None
        except jwt.InvalidSignatureError:
            raise TokenInvalidException("Invalid token signature") from None
        except jwt.InvalidTokenError as e:
            raise TokenInvalidException(f"Invalid token: {e!s}") from e
        except Exception as e:
            raise TokenInvalidException(f"Token decode failed: {e!s}") from e

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without full validation."""
        try:
            # Extract claims without signature verification
            claims = jwt.decode(token, options={"verify_signature": False})
            exp    = claims.get("exp")
            if not exp:
                return True
            return datetime.now(timezone.utc).timestamp() > exp
        except Exception:
            return True

    def create_expiry(self, minutes: Optional[int] = None, days: Optional[int] = None) -> datetime:
        """Create expiry datetime for token."""
        now = datetime.now(timezone.utc)

        if minutes:
            return now + timedelta(minutes=minutes)
        elif days:
            return now + timedelta(days=days)
        else:
            return now + timedelta(minutes=self.jwt_config.access_token_expire_minutes)
