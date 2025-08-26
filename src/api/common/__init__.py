"""Common API components for reuse across models."""

from .dependencies import get_current_tenant
from .router_utils import CRUDRouterFactory
from .router_utils import SearchableRouterMixin
from .schemas import BaseCreateSchema
from .schemas import BaseResponseSchema
from .schemas import BaseUpdateSchema
from .schemas import ErrorResponse
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
