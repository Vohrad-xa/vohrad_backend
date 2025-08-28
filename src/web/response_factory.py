"""Centralized response factory for consistent API responses."""

from .pagination import PaginatedResponse
from .responses import CreatedResponse
from .responses import DeletedResponse
from .responses import SuccessResponse
from pydantic import BaseModel
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

T = TypeVar("T", bound=BaseModel)

class ResponseFactory:
    """Factory class for creating consistent API responses."""

    @staticmethod

    def success(data: Union[T, List[T]], message: Optional[str] = None) -> SuccessResponse[Union[T, List[T]]]:
        """Create a success response with data."""
        return SuccessResponse(data=data, message=message)

    @staticmethod

    def created(data: T, message: Optional[str] = None) -> CreatedResponse[T]:
        """Create a success response for resource creation."""
        if message:
            return CreatedResponse(data=data, message=message)
        else:
            return CreatedResponse(data=data)

    @staticmethod

    def deleted(message: Optional[str] = None) -> DeletedResponse:
        """Create a success response for resource deletion."""
        if message:
            return DeletedResponse(message=message)
        else:
            return DeletedResponse()

    @staticmethod

    def paginated(data: PaginatedResponse[T]) -> SuccessResponse[PaginatedResponse[T]]:
        """Create a success response for paginated data."""
        return SuccessResponse(data=data)

    @staticmethod

    def transform_and_respond(
        data: Union[object, List[object]], response_model: Type[T], response_type: str = "success"
    ) -> Union[SuccessResponse[Union[T, List[T]]], CreatedResponse[T]]:
        """Transform data to response model and create appropriate response.

        Args:
            data: Raw data object or list of objects
            response_model: Pydantic model to transform to
            response_type: "success" or "created"
        """
        if isinstance(data, list):
            transformed_data = [response_model.model_validate(item) for item in data]
        else:
            transformed_data = response_model.model_validate(data)

        if response_type == "created":
            if isinstance(transformed_data, list):
                # For created responses, we expect a single item, not a list
                # If we have a list, take the first item or handle appropriately
                if transformed_data:
                    return ResponseFactory.created(transformed_data[0])
                else:
                    raise ValueError("Cannot create response from empty list")
            else:
                return ResponseFactory.created(transformed_data)
        else:
            return ResponseFactory.success(transformed_data)
