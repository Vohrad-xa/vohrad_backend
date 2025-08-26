"""Exception handlers with structured logging."""

import logging
from datetime import datetime
from datetime import timezone
from exceptions import ApplicationException
from exceptions import BaseAppException
from exceptions import DomainException
from exceptions import InfrastructureException
from exceptions import IntegrationException
from fastapi import Request
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from typing import Any
from typing import Dict
from uuid import uuid4

logger = logging.getLogger(__name__)

class EnterpriseExceptionHandler:
    """Exception handler with structured logging and observability."""

    @staticmethod

    def _generate_correlation_id(exc: BaseAppException) -> str:
        """Generate or retrieve correlation ID."""
        return exc.correlation_id or str(uuid4())

    @staticmethod

    def _extract_request_metadata(request: Request) -> Dict[str, Any]:
        """Extract standardized request metadata."""
        return {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod

    def _create_error_response(
        error_code: str, message: str, exception_type: str, correlation_id: str, details: Dict[str, Any], timestamp: str
    ) -> Dict[str, Any]:
        """Create standardized error response structure."""
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "type": exception_type,
                "correlation_id": correlation_id,
                "details": details,
            },
            "metadata": {"timestamp": timestamp, "correlation_id": correlation_id},
        }

    @staticmethod

    def _format_validation_errors(errors) -> list:
        """Convert validation errors to standardized format."""
        validation_errors = []
        for error in errors:
            validation_errors.append(
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", ""),
                    "type": error.get("type", ""),
                    "input": error.get("input"),
                }
            )
        return validation_errors

    @staticmethod
    async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        """Handle application exceptions with structured metadata."""
        correlation_id = EnterpriseExceptionHandler._generate_correlation_id(exc)
        request_metadata = EnterpriseExceptionHandler._extract_request_metadata(request)

        error_response = EnterpriseExceptionHandler._create_error_response(
            exc.error_code,
            exc.message,
            exc.__class__.__name__,
            correlation_id,
            exc.details,
            request_metadata["timestamp"],
        )

        # Log based on exception layer
        log_data = {
            "exception_type": exc.__class__.__name__,
            "error_code": exc.error_code,
            "exception_message": exc.message,
            "status_code": exc.status_code,
            "correlation_id": correlation_id,
            "request": request_metadata,
            "details": exc.details,
        }

        if isinstance(exc, (DomainException, ApplicationException)):
            logger.info("Domain/Application exception", extra=log_data)
        elif isinstance(exc, InfrastructureException):
            logger.warning("Infrastructure exception", extra=log_data)
        elif isinstance(exc, IntegrationException):
            logger.warning("Integration exception", extra=log_data)
        else:
            logger.error("Unexpected application exception", extra=log_data)

        return JSONResponse(status_code=exc.status_code, content=error_response)

    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle FastAPI validation errors."""
        correlation_id = str(uuid4())
        request_metadata = EnterpriseExceptionHandler._extract_request_metadata(request)
        validation_errors = EnterpriseExceptionHandler._format_validation_errors(exc.errors())

        error_response = EnterpriseExceptionHandler._create_error_response(
            "VALIDATION_ERROR",
            "Request validation failed",
            "RequestValidationError",
            correlation_id,
            {"validation_errors": validation_errors},
            request_metadata["timestamp"],
        )

        logger.info(
            "Request validation failed",
            extra={
                "correlation_id": correlation_id,
                "validation_errors": validation_errors,
                "request_url": str(request.url),
                "request_method": request.method,
            },
        )

        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response)

    @staticmethod
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        correlation_id = str(uuid4())
        request_metadata = EnterpriseExceptionHandler._extract_request_metadata(request)
        validation_errors = EnterpriseExceptionHandler._format_validation_errors(exc.errors())

        error_response = EnterpriseExceptionHandler._create_error_response(
            "PYDANTIC_VALIDATION_ERROR",
            "Data validation failed",
            "PydanticValidationError",
            correlation_id,
            {"validation_errors": validation_errors},
            request_metadata["timestamp"],
        )

        logger.info(
            "Pydantic validation failed",
            extra={
                "correlation_id": correlation_id,
                "validation_errors": validation_errors,
                "request_url": str(request.url),
                "request_method": request.method,
            },
        )

        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response)

    @staticmethod
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        correlation_id = str(uuid4())
        request_metadata = EnterpriseExceptionHandler._extract_request_metadata(request)

        error_response = EnterpriseExceptionHandler._create_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            "InternalServerError",
            correlation_id,
            {},
            request_metadata["timestamp"],
        )

        logger.error(
            "Unexpected server error occurred",
            extra={
                "correlation_id": correlation_id,
                "exception_type": exc.__class__.__name__,
                "exception_message": str(exc),
                "request_url": str(request.url),
                "request_method": request.method,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
            exc_info=True,
        )

        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_response)
