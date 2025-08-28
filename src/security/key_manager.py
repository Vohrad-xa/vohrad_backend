"""Secure key management utilities for encryption and JWT operations."""

import base64
import secrets
from config.settings import get_settings
from cryptography.fernet import Fernet
from typing import Optional

class KeyManager:
    """Centralized key management for encryption and JWT operations."""

    def __init__(self):
        self.settings = get_settings()
        self._encryption_key: Optional[bytes] = None

    @property

    def jwt_secret_key(self) -> str:
        """Get JWT secret key with validation."""
        if not self.settings.SECRET_KEY:
            raise ValueError("SECRET_KEY not configured")
        return self.settings.SECRET_KEY

    @property

    def jwt_algorithm(self) -> str:
        """Get JWT algorithm."""
        return self.settings.JWT_ALGORITHM

    def get_encryption_key(self) -> bytes:
        """Get or generate encryption key for sensitive data."""
        if self._encryption_key is None:
            if self.settings.ENCRYPTION_KEY:
                # Use provided encryption key
                try:
                    self._encryption_key = base64.urlsafe_b64decode(self.settings.ENCRYPTION_KEY)
                except Exception:
                    raise ValueError("Invalid ENCRYPTION_KEY format - must be base64 encoded") from None
            else:
                # Generate encryption key from SECRET_KEY
                self._encryption_key = self._derive_encryption_key()

        return self._encryption_key

    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from SECRET_KEY using secure method."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        # Use fixed salt for deterministic key derivation
        # In production, consider using a configurable salt
        salt = b"vohrad_encryption_salt_v1"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits
            salt=salt,
            iterations=100000,  # NIST recommended minimum
        )

        return kdf.derive(self.settings.SECRET_KEY.encode())

    def create_fernet(self) -> Fernet:
        """Create Fernet cipher for symmetric encryption."""
        key = base64.urlsafe_b64encode(self.get_encryption_key())
        return Fernet(key)

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like PII, tokens, etc."""
        fernet = self.create_fernet()
        encrypted_bytes = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        fernet = self.create_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()

    @staticmethod

    def generate_secret_key() -> str:
        """Generate a cryptographically secure secret key."""
        return secrets.token_urlsafe(64)

    @staticmethod

    def generate_encryption_key() -> str:
        """Generate a base64-encoded encryption key."""
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()

    def validate_keys(self) -> dict:
        """Validate all configured keys and return status."""
        status = {
            "secret_key_configured": bool(self.settings.SECRET_KEY),
            "secret_key_length": len(self.settings.SECRET_KEY) if self.settings.SECRET_KEY else 0,
            "secret_key_strength": "strong"
            if (
                self.settings.SECRET_KEY
                and len(self.settings.SECRET_KEY) >= 64
                and not self.settings.SECRET_KEY.isalnum()
            )
            else "weak",
            "encryption_key_configured": bool(self.settings.ENCRYPTION_KEY),
            "jwt_algorithm": self.settings.JWT_ALGORITHM,
            "environment": self.settings.ENVIRONMENT,
        }

        # Security warnings
        warnings = []
        if self.settings.ENVIRONMENT == "production":
            if not self.settings.SECRET_KEY:
                warnings.append("SECRET_KEY required for production")
            elif len(self.settings.SECRET_KEY) < 32:
                warnings.append("SECRET_KEY too short for production")
            elif self.settings.SECRET_KEY.isalnum():
                warnings.append("SECRET_KEY should contain special characters")

        status["warnings"] = warnings
        return status

# Global instance
_key_manager = KeyManager()

def get_key_manager() -> KeyManager:
    """Get the global key manager instance."""
    return _key_manager
