"""Authentication utilities for password hashing and verification."""

from typing import ClassVar, Optional
from passlib.context import CryptContext

class PasswordManager:
    """Centralized password hashing and verification utility."""

    _instance: ClassVar[Optional["PasswordManager"]] = None
    _pwd_context: ClassVar[Optional[CryptContext]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return cls._instance

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        assert self._pwd_context is not None
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        assert self._pwd_context is not None
        return self._pwd_context.verify(plain_password, hashed_password)

# Create a global instance for easy importing
password_manager = PasswordManager()

# Convenience functions for backward compatibility
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return password_manager.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return password_manager.verify_password(plain_password, hashed_password)
