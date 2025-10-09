"""Admin service for admin user management."""

from .models import Admin
from api.common import BaseService
from typing import Any


class AdminService(BaseService[Admin, Any, Any]):
    """Admin operations."""

    def __init__(self):
        super().__init__(Admin)


    def get_search_fields(self) -> list[str]:
        """Return searchable fields."""
        return ["email", "first_name", "last_name", "role"]


admin_service = AdminService()
