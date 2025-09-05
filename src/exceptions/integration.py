"""Integration exceptions for third-party services."""

from .base import BaseAppException
from fastapi import status
from typing import Any, Dict, Optional


class IntegrationException(BaseAppException):
    """Base class for external system integration exceptions."""

    def __init__(
    self,
    message    : str,
    error_code : str,
    status_code: int = status.HTTP_502_BAD_GATEWAY,
    details    : Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class ThirdPartyAPIException(IntegrationException):
    """Third-party API communication failures."""

    def __init__(
        self,
        api_name     : str,
        endpoint     : str,
        http_status  : int,
        response_body: Optional[str] = None,
        details      : Optional[Dict[str, Any]] = None,
    ):
        error_details = {"api_name": api_name, "endpoint": endpoint, "http_status": http_status}
        if response_body:
            error_details["response_body"] = response_body
        if details:
            error_details.update(details)

        super().__init__(
            message    = f"Third-party API '{api_name}' failed at {endpoint} (HTTP {http_status})",
            error_code = "THIRD_PARTY_API_ERROR",
            details    = error_details,
        )


class PaymentGatewayException(IntegrationException):
    """Payment gateway integration failures."""

    def __init__(
        self,
        gateway           : str,
        operation         : str,
        gateway_error_code: Optional[str] = None,
        details           : Optional[Dict[str, Any]] = None,
    ):
        error_details = {"gateway": gateway, "operation": operation}
        if gateway_error_code:
            error_details["gateway_error_code"] = gateway_error_code
        if details:
            error_details.update(details)

        super().__init__(
            message    = f"Payment gateway '{gateway}' failed during {operation}",
            error_code = "PAYMENT_GATEWAY_ERROR",
            details    = error_details,
        )


class EmailServiceException(IntegrationException):
    """Email service integration failures."""

    def __init__(
        self,
        provider : str,
        operation: str,
        recipient: Optional[str] = None,
        details  : Optional[Dict[str, Any]] = None,
    ):
        error_details = {"provider": provider, "operation": operation}
        if recipient:
            error_details["recipient"] = recipient
        if details:
            error_details.update(details)

        super().__init__(
            message    = f"Email service '{provider}' failed during {operation}",
            error_code = "EMAIL_SERVICE_ERROR",
            details    = error_details,
        )


class MessageQueueException(IntegrationException):
    """Message queue integration failures."""

    def __init__(
        self,
    queue_name: str,
    operation : str,
    message_id: Optional[str] = None,
    details   : Optional[Dict[str, Any]] = None,
    ):
        error_details = {"queue_name": queue_name, "operation": operation}
        if message_id:
            error_details["message_id"] = message_id
        if details:
            error_details.update(details)

        super().__init__(
            message    = f"Message queue '{queue_name}' failed during {operation}",
            error_code = "MESSAGE_QUEUE_ERROR",
            details    = error_details,
        )
