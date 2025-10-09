"""FastAPI application setup (routers, middleware, handlers)."""

from api.admin import routes as admin_routes
from api.auth import AuthMiddleware, router as auth_routes
from api.item.router import routes as item_routes
from api.item_location.models import ItemLocation  # noqa: F401
from api.item_location.router import routes as item_location_routes
from api.license.router import routes as license_routes
from api.location.models import Location  # noqa: F401
from api.location.router import routes as location_routes
from api.permission.router import routes as permission_routes
from api.role.router import routes as role_routes
from api.stripe.router import routes as webhook_routes
from api.system.router import routes as system_routes
from api.tenant.router import routes as tenant_routes
from api.user.router import routes as user_routes
from config import get_settings, install_cors, install_rate_limiting
from contextlib import asynccontextmanager
from exceptions import BaseAppException
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from middleware import ExceptionHandler
from middleware.logging_middleware import RequestLoggingMiddleware
from observability import get_logger, setup_logging
from pydantic import ValidationError as PydanticValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: RUF029
    settings = get_settings()
    setup_logging({"ENVIRONMENT": settings.ENVIRONMENT, "LOG_LEVEL": getattr(settings, "LOG_LEVEL", "INFO")})
    logger = get_logger("vohrad.startup")
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


settings = get_settings()


app = FastAPI(
    title       = "Vohrad API",
    description = "Inventory and Asset Management Backend API",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    AuthMiddleware,
    excluded_paths={
        "/v1/system/health",
        "/v1/auth/login/user",
        "/v1/auth/login/admin",
        "/v1/auth/refresh",
        "/v1/auth/status",
        "/webhooks/stripe",
    },
    auto_error=True,
)


app.add_middleware(RequestLoggingMiddleware)

install_cors(app)
install_rate_limiting(app)
app.add_exception_handler(BaseAppException, ExceptionHandler.base_app_exception_handler)
app.add_exception_handler(RequestValidationError, ExceptionHandler.validation_exception_handler)
app.add_exception_handler(PydanticValidationError, ExceptionHandler.pydantic_validation_exception_handler)
app.add_exception_handler(Exception, ExceptionHandler.generic_exception_handler)

app.include_router(webhook_routes)
app.include_router(auth_routes, prefix="/v1")
app.include_router(admin_routes, prefix="/v1")
app.include_router(tenant_routes, prefix="/v1")
app.include_router(user_routes, prefix="/v1")
app.include_router(role_routes, prefix="/v1")
app.include_router(permission_routes, prefix="/v1")
app.include_router(license_routes, prefix="/v1")
app.include_router(item_routes, prefix="/v1")
app.include_router(item_location_routes, prefix="/v1")
app.include_router(location_routes, prefix="/v1")
app.include_router(system_routes, prefix="/v1")
