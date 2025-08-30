"""Authentication utilities for password hashing and verification."""


from passlib.context import CryptContext
from typing import ClassVar
from typing import Optional


class PasswordManager:
    """Centralized password hashing and verification utility."""

    _instance: ClassVar[Optional["PasswordManager"]] = None
    _pwd_context: ClassVar[Optional[CryptContext]]   = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance    = super().__new__(cls)
            cls._pwd_context = CryptContext(
                schemes            = ["bcrypt"],
                deprecated         = "auto",
                bcrypt__min_rounds = 12
            )
        return cls._instance

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        assert self._pwd_context is not None
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        assert self._pwd_context is not None
        return self._pwd_context.verify(plain_password, hashed_password)


password_manager = PasswordManager()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return password_manager.verify_password(plain_password, hashed_password)
