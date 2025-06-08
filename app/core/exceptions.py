"""
app/core/exceptions.py

This module defines custom exceptions used across the application for standardized
error handling. These exceptions will be caught by FastAPI exception handlers
to return consistent error responses.
"""

from fastapi import HTTPException, status

class TankControllerException(HTTPException):
    """Base exception for Tank Controller application."""
    def __init__(self, status_code: int, detail: str, headers: dict | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class TankNotFoundError(TankControllerException):
    """Exception raised when a specified tank cannot be found."""
    def __init__(self, detail: str = "Tank not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class CommandNotFoundError(TankControllerException):
    """Exception raised when a specified command cannot be found."""
    def __init__(self, detail: str = "Command not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class InvalidCommandError(TankControllerException):
    """Exception raised when an invalid command payload is provided."""
    def __init__(self, detail: str = "Invalid command payload"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class AuthenticationError(TankControllerException):
    """Exception raised for authentication failures."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ForbiddenError(TankControllerException):
    """Exception raised when access is forbidden."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class ConflictError(TankControllerException):
    """Exception raised for resource conflicts."""
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class ServiceUnavailableError(TankControllerException):
    """Exception raised when a service is temporarily unavailable."""
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

class InternalServerError(TankControllerException):
    """Exception raised for unexpected internal server errors."""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class DatabaseError(Exception):
    def __init__(self, detail: str = "Database error"):
        self.status_code = 500
        self.detail = detail 