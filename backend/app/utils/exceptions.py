"""Centralized Application Exceptions."""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class UnauthorizedException(AppException):
    """401 Unauthorized exception."""

    def __init__(
        self,
        message: str = "Authentication required. Please sign in to continue.",
        error_code: str = "UNAUTHORIZED",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            details=details,
        )


class ForbiddenException(AppException):
    """403 Forbidden exception for role and access barriers."""

    def __init__(
        self,
        message: str = "Access forbidden. Insufficient permissions for this resource.",
        error_code: str = "FORBIDDEN",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details,
        )


class VerificationRequiredException(AppException):
    """403 Forbidden exception specifically for unverified accounts."""

    def __init__(
        self,
        message: str = "Your account is awaiting verification. Restricted operational actions are not permitted until verified.",
        error_code: str = "VERIFICATION_REQUIRED",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details,
        )


class NotFoundException(AppException):
    """404 Not Found exception."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        error_code: str = "NOT_FOUND",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            details=details,
        )


class ConflictException(AppException):
    """409 Conflict exception."""

    def __init__(
        self,
        message: str = "A resource conflict occurred.",
        error_code: str = "CONFLICT",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            details=details,
        )


class ValidationException(AppException):
    """422 Validation exception."""

    def __init__(
        self,
        message: str = "Invalid input data provided.",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code=error_code,
            details=details,
        )
