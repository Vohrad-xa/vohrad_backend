from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from api.system.router import routes as system_routes
from api.tenant.router import routes as tenant_routes
from api.user.router import routes as user_routes
from config.settings import get_settings
from exceptions import BaseAppException
from middleware import EnterpriseExceptionHandler
from middleware.logging_middleware import RequestLoggingMiddleware
from observability import get_logger, setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: RUF029
    settings = get_settings()
    setup_logging({"ENVIRONMENT": settings.ENVIRONMENT, "LOG_LEVEL": getattr(settings, "LOG_LEVEL", "INFO")})

    logger = get_logger("vohrad.startup")
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")

app = FastAPI(
    title="Vohrad API",
    description="Multi-tenant FastAPI application with enterprise logging",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_exception_handler(BaseAppException, EnterpriseExceptionHandler.base_app_exception_handler)
app.add_exception_handler(RequestValidationError, EnterpriseExceptionHandler.validation_exception_handler)
app.add_exception_handler(PydanticValidationError, EnterpriseExceptionHandler.pydantic_validation_exception_handler)
app.add_exception_handler(Exception, EnterpriseExceptionHandler.generic_exception_handler)

app.include_router(tenant_routes, prefix="/v1")
app.include_router(user_routes, prefix="/v1")
app.include_router(system_routes, prefix="/v1")
