"""Common API components for reuse across models."""

from .base_router import BaseRouterMixin
from .base_router import SharedScopedRouterMixin
from .base_router import StandardRouterPatterns
from .base_router import TenantScopedRouterMixin
from .context_dependencies import get_authenticated_context
from .context_dependencies import get_shared_context
from .context_dependencies import get_tenant_context
from .schemas import BaseCreateSchema
from .schemas import BaseResponseSchema
from .schemas import BaseUpdateSchema
from .schemas import ErrorResponse
from .validators import CommonValidators

__all__ = [
    "BaseCreateSchema",
    "BaseResponseSchema",
    "BaseRouterMixin",
    "BaseUpdateSchema",
    "CommonValidators",
    "ErrorResponse",
    "SharedScopedRouterMixin",
    "StandardRouterPatterns",
    "TenantScopedRouterMixin",
    "get_authenticated_context",
    "get_shared_context",
    "get_tenant_context",
]
