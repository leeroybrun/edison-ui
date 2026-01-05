"""Error response schemas for API endpoints.

Provides consistent error response structures across the API.
"""

from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detail information about a single error.

    Attributes:
        code: Machine-readable error code (e.g., "VALIDATION_ERROR").
        message: Human-readable error message.
        field: Optional field name if the error is field-specific.
    """

    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper.

    Attributes:
        error: The error detail.
        request_id: Optional request ID for debugging.
    """

    error: ErrorDetail
    request_id: str | None = None


class ValidationErrorResponse(BaseModel):
    """Response for validation errors with multiple issues.

    Attributes:
        errors: List of validation error details.
        request_id: Optional request ID for debugging.
    """

    errors: list[ErrorDetail]
    request_id: str | None = None
