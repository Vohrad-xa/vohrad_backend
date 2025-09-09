"""Centralized response factory for consistent API responses."""

from .responses import CreatedResponse, DeletedResponse, SuccessResponse, UpdatedResponse
from pydantic import BaseModel
from typing import Any, List, Optional, Type, TypeVar, Union

T = TypeVar("T", bound=BaseModel)


class ResponseFactory:
    """Factory class for creating consistent API responses."""

    @staticmethod
    def success(
        data: Union[T, List[T], object],
        message: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
    ) -> SuccessResponse[Any]:
        """Create a success response with smart message generation."""
        transformed_data = ResponseFactory._transform_data(data, response_model)

        if message is None and response_model is not None:
            message = ResponseFactory._generate_message(response_model, "retrieved", data)

        return SuccessResponse(data=transformed_data, message=message)

    @staticmethod
    def created(
        data: Union[T, object],
        message: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
    ) -> CreatedResponse[T]:
        """Create a created response with smart message generation."""
        transformed_data = ResponseFactory._transform_data(data, response_model)

        if message is None and response_model is not None:
            message = ResponseFactory._generate_message(response_model, "created")

        if message is None:
            return CreatedResponse(data=transformed_data)
        return CreatedResponse(data=transformed_data, message=message)

    @staticmethod
    def updated(
        data: Union[T, object],
        message: Optional[str] = None,
        response_model: Optional[Type[T]] = None,
    ) -> UpdatedResponse[T]:
        """Create an updated response with smart message generation."""
        transformed_data = ResponseFactory._transform_data(data, response_model)

        if message is None and response_model is not None:
            message = ResponseFactory._generate_message(response_model, "updated")

        if message is None:
            return UpdatedResponse(data=transformed_data)
        return UpdatedResponse(data=transformed_data, message=message)

    @staticmethod
    def deleted(resource_name: Optional[str] = None) -> DeletedResponse:
        """Create a deleted response."""
        if resource_name:
            message = f"{resource_name.capitalize()} deleted successfully"
            return DeletedResponse(message=message)
        return DeletedResponse()

    @staticmethod
    def _transform_data(data: Union[T, List[T], object], response_model: Optional[Type[T]]) -> Union[T, List[T], object]:
        """Transform data using response model if provided."""
        if response_model is None:
            return data

        if isinstance(data, BaseModel):
            return data

        if isinstance(data, list):
            return [response_model.model_validate(item) for item in data]

        if hasattr(data, "items") and hasattr(data, "total"):
            return data

        return response_model.model_validate(data)

    @staticmethod
    def _extract_resource_name(response_model: Type[T]) -> str:
        """Extract resource name from response model class name."""
        name = response_model.__name__
        if name.endswith("Response"):
            name = name[:-8]
        return name.lower()

    @staticmethod
    def _generate_message(response_model: Type[T], action: str, data: Union[T, List[T], None] = None) -> str:
        """Generate contextual messages based on response model and action."""
        resource_name = ResponseFactory._extract_resource_name(response_model)

        if action == "retrieved":
            # Handle paginated responses
            if hasattr(data, "total") and hasattr(data, "items"):
                total = data.total
                if total == 0:
                    return f"No {resource_name}s available"
                elif total == 1:
                    return f"{resource_name.capitalize()} retrieved successfully"
                else:
                    return f"{total} {resource_name}s retrieved successfully"
            # Handle regular lists
            elif isinstance(data, list):
                if not data:
                    return f"No {resource_name}s available"
                elif len(data) == 1:
                    return f"{resource_name.capitalize()} retrieved successfully"
                else:
                    return f"{len(data)} {resource_name}s retrieved successfully"
            elif data is None:
                return f"No {resource_name} available"
            else:
                return f"{resource_name.capitalize()} retrieved successfully"

        return f"{resource_name.capitalize()} {action} successfully"
