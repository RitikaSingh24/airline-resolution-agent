"""Application custom exceptions and global exception handlers."""

import logging

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("airline_resolution")


class AppException(HTTPException):
    """Base application domain exception."""

    def __init__(
        self,
        message: str = "An application error occurred",
        error_type: str = "AppError",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            error_type="NotFound",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class BadRequestException(AppException):
    """Bad request exception."""

    def __init__(self, message: str = "Invalid request"):
        super().__init__(
            message=message,
            error_type="BadRequest",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handles custom AppException instances."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_type, "message": exc.message},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles standard FastAPI HTTPException instances."""
    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_type, "message": exc.message},
        )
    error_type = "NotFound" if exc.status_code == 404 else "HTTPError"
    message = str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_type, "message": message},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles Pydantic request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled exceptions and prevents stack trace leakage."""
    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_type, "message": exc.message},
        )
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected internal server error occurred.",
        },
    )
