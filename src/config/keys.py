"""Key management utilities for encryption and JWT operations."""

import base64
from config.settings import get_settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
from pathlib import Path
import secrets
from typing import Optional, Union


class KeyManager:
    """Centralized key management for encryption and JWT operations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._encryption_key: Optional[bytes] = None

    @property
    def jwt_private_key(self) -> bytes:
        """Get JWT private key for RS256 signing."""
        if self.settings.JWT_PRIVATE_KEY_PATH and os.path.exists(self.settings.JWT_PRIVATE_KEY_PATH):
            with open(self.settings.JWT_PRIVATE_KEY_PATH, "rb") as key_file:
                return key_file.read()
        else:
            # Generate RSA key pair if not found (development only)
            if self.settings.ENVIRONMENT == "development":
                return self._generate_or_load_dev_keys()[0]
            else:
                raise ValueError("JWT_PRIVATE_KEY_PATH not configured for production")

    @property
    def jwt_public_key(self) -> bytes:
        """Get JWT public key for RS256 verification."""
        if self.settings.JWT_PUBLIC_KEY_PATH and os.path.exists(self.settings.JWT_PUBLIC_KEY_PATH):
            with open(self.settings.JWT_PUBLIC_KEY_PATH, "rb") as key_file:
                return key_file.read()
        else:
            # Generate RSA key pair if not found (development only)
            if self.settings.ENVIRONMENT == "development":
                return self._generate_or_load_dev_keys()[1]
            else:
                raise ValueError("JWT_PUBLIC_KEY_PATH not configured for production")

    @property
    def jwt_secret_key(self) -> Union[str, bytes]:
        """Get JWT signing key (RS256 uses private key, HS256 uses secret)."""
        if self.settings.JWT_ALGORITHM.startswith("RS") or self.settings.JWT_ALGORITHM.startswith("ES"):
            return self.jwt_private_key
        else:
            if not self.settings.SECRET_KEY:
                raise ValueError("SECRET_KEY not configured")
            return self.settings.SECRET_KEY

    @property
    def jwt_verify_key(self) -> Union[str, bytes]:
        """Get JWT verification key (RS256 uses public key, HS256 uses secret)."""
        if self.settings.JWT_ALGORITHM.startswith("RS") or self.settings.JWT_ALGORITHM.startswith("ES"):
            return self.jwt_public_key
        else:
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
            if hasattr(self.settings, "ENCRYPTION_KEY") and self.settings.ENCRYPTION_KEY:
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
        # Use fixed salt for deterministic key derivation
        # In production: configurable salt
        salt = b"vohrad_encryption_salt_v1"

        kdf = PBKDF2HMAC(
            algorithm  = hashes.SHA256(),
            length     = 32,              # 32 bytes = 256 bits
            salt       = salt,
            iterations = 100000,          # NIST recommended minimum
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

    def _generate_or_load_dev_keys(self) -> tuple[bytes, bytes]:
        """Generate or load RSA key pair for development."""
        dev_keys_dir = Path(".dev_keys")
        dev_keys_dir.mkdir(exist_ok=True)

        private_key_path = dev_keys_dir / "jwt_private.pem"
        public_key_path = dev_keys_dir / "jwt_public.pem"

        if private_key_path.exists() and public_key_path.exists():
            # Load existing keys
            with open(private_key_path, "rb") as f:
                private_key_bytes = f.read()
            with open(public_key_path, "rb") as f:
                public_key_bytes = f.read()
            return private_key_bytes, public_key_bytes

        # Generate new RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Serialize private key
        private_key_bytes = private_key.private_bytes(
            encoding             = serialization.Encoding.PEM,
            format               = serialization.PrivateFormat.PKCS8,
            encryption_algorithm = serialization.NoEncryption(),
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Save keys to files
        with open(private_key_path, "wb") as f:
            f.write(private_key_bytes)
        with open(public_key_path, "wb") as f:
            f.write(public_key_bytes)

        return private_key_bytes, public_key_bytes

    @staticmethod
    def generate_secret_key() -> str:
        """Generate a cryptographically secure secret key."""
        return secrets.token_urlsafe(64)

    @staticmethod
    def generate_rsa_key_pair() -> tuple[str, str]:
        """Generate RSA key pair for JWT signing."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding             = serialization.Encoding.PEM,
            format               = serialization.PrivateFormat.PKCS8,
            encryption_algorithm = serialization.NoEncryption(),
        ).decode("utf-8")

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        return private_pem, public_pem

    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a base64-encoded encryption key."""
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()

    def validate_keys(self) -> dict:
        """Validate all configured keys and return status."""
        status = {
            "secret_key_configured": bool(self.settings.SECRET_KEY),
            "secret_key_length"    : len(self.settings.SECRET_KEY) if self.settings.SECRET_KEY else 0,
            "secret_key_strength"  : "strong"
            if (self.settings.SECRET_KEY and len(self.settings.SECRET_KEY) >= 64 and not self.settings.SECRET_KEY.isalnum())
            else "weak",
            "encryption_key_configured": bool(getattr(self.settings, "ENCRYPTION_KEY", None)),
            "jwt_algorithm"            : self.settings.JWT_ALGORITHM,
            "environment"              : self.settings.ENVIRONMENT,
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
