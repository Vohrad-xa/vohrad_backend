"""Common API components for reuse across models."""

from .dependencies import get_current_tenant
from .router_utils import CRUDRouterFactory, SearchableRouterMixin
from .schemas import BaseCreateSchema, BaseResponseSchema, BaseUpdateSchema, ErrorResponse
from .validators import CommonValidators

__all__ = [
    "BaseCreateSchema",
    "BaseResponseSchema",
    "BaseUpdateSchema",
    "CRUDRouterFactory",
    "CommonValidators",
    "ErrorResponse",
    "SearchableRouterMixin",
    "get_current_tenant",
]
