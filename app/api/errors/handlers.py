from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.api.utils.responses import create_error_response

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    details = {"errors": exc.errors()}
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Invalid request parameters",
        details=details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    return create_error_response(
        code="DATABASE_ERROR",
        message="Database operation failed",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return create_error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ) 