"""Common validation functions reusable across all models."""

from bleach import clean  # type: ignore[import-untyped]
from constants import ValidationConstraints, ValidationMessages
import json
from typing import Optional


class CommonValidators:
    """Collection of reusable validation methods for consistent validation across models."""

    @staticmethod
    def validate_name_field(v: Optional[str], field_name: str = "Name") -> Optional[str]:
        """Validate name fields (first_name, last_name, etc.) with consistent rules."""
        if v is not None:
            if len(v) > ValidationConstraints.MAX_NAME_LENGTH:
                raise ValueError(f"{field_name} {ValidationMessages.NAME_TOO_LONG}")
            elif len(v) < ValidationConstraints.MIN_NAME_LENGTH:
                raise ValueError(f"{field_name} {ValidationMessages.NAME_TOO_SHORT}")
        return v

    @staticmethod
    def validate_password_strength(v: str) -> str:
        """Validate password strength with consistent rules."""
        if len(v) < ValidationConstraints.MIN_PASSWORD_LENGTH:
            raise ValueError(ValidationMessages.PASSWORD_TOO_SHORT)
        elif len(v) > ValidationConstraints.MAX_PASSWORD_LENGTH:
            raise ValueError(ValidationMessages.PASSWORD_TOO_LONG)

        if not any(c.isupper() for c in v):
            raise ValueError(ValidationMessages.PASSWORD_MISSING_UPPERCASE)

        if not any(c in ValidationConstraints.SPECIAL_CHARS for c in v):
            raise ValueError(ValidationMessages.PASSWORD_MISSING_SPECIAL)

        return v

    @staticmethod
    def validate_phone_number(v: Optional[str]) -> Optional[str]:
        """Validate phone number format and length."""
        if v is not None and len(v) > ValidationConstraints.MAX_PHONE_LENGTH:
            raise ValueError(ValidationMessages.PHONE_TOO_LONG)
        return v

    @staticmethod
    def validate_role_field(
        v         : Optional[str],
        max_length: int = ValidationConstraints.DEFAULT_ROLE_LENGTH
    ) -> Optional[str]:
        """Validate role fields with configurable max length."""
        if v is not None and len(v) > max_length:
            raise ValueError(f"Role must be {max_length} characters or less")
        return v

    @staticmethod
    def validate_text_field_length(
        v         : Optional[str],
        max_length: int,
        field_name: str = "Field"
    ) -> Optional[str]:
        """Generic text field length validation."""
        if v is not None and len(v) > max_length:
            raise ValueError(f"{field_name} must be {max_length} characters or less")
        return v

    @staticmethod
    def validate_required_string(v: Optional[str], field_name: str = "Field") -> str:
        """Validate that a string field is not None or empty."""
        if not v or not v.strip():
            raise ValueError(f"{field_name} is required")
        return v.strip()

    @staticmethod
    def validate_password_confirmation(confirm_password: str, password: str) -> str:
        """Validate password confirmation matches."""
        if confirm_password != password:
            raise ValueError("Password confirmation does not match")
        return confirm_password

    @staticmethod
    def validate_jsonb_specifications(v: Optional[dict]) -> Optional[dict]:
        """JSONB validation."""
        if v is None:
            return v

        # Size limit
        json_str = json.dumps(v)
        if len(json_str) > 50000:
            raise ValueError("Specifications data too large (max 50KB)")

        # Depth validation
        def get_depth(obj, current_depth=1, max_depth=5):
            if current_depth > max_depth:
                raise ValueError(f"Specifications nested too deep (max {max_depth} levels)")
            if isinstance(obj, dict):
                return max((get_depth(val, current_depth + 1, max_depth) for val in obj.values()), default=current_depth)
            if isinstance(obj, list):
                return max((get_depth(item, current_depth + 1, max_depth) for item in obj), default=current_depth)
            return current_depth

        get_depth(v)


        def validate_keys(obj):
            if isinstance(obj, dict):
                for key in obj.keys():
                    if not isinstance(key, str):
                        raise ValueError(f"Invalid key type: {type(key).__name__}")
                    if not all(c.isalnum() or c in ('_', '-') for c in key):
                        raise ValueError(f"Invalid key format: '{key}'")
                    if len(key) > 100:
                        raise ValueError(f"Key too long: '{key}'")
                    validate_keys(obj[key])
            elif isinstance(obj, list):
                for item in obj:
                    validate_keys(item)

        validate_keys(v)

        # Sanitize values using bleach
        def sanitize_values(obj):
            if isinstance(obj, str):
                # Strip ALL HTML tags and attributes
                sanitized = clean(obj, tags=[], attributes={}, strip=True)
                if len(sanitized) > 5000:
                    raise ValueError("String value too long (max 5000 chars)")
                return sanitized
            elif isinstance(obj, dict):
                return {k: sanitize_values(val) for k, val in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_values(item) for item in obj]
            return obj

        return sanitize_values(v)
