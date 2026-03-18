import logging
import traceback
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("api")


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class BadRequestError(AppError):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message=message, status_code=400, error_code="BAD_REQUEST")

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED")

class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN")

class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: int | str | None = None):
        msg = f"{resource} with id {resource_id} not found" if resource_id else f"{resource} not found"
        super().__init__(message=msg, status_code=404, error_code="NOT_FOUND")

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=409, error_code="CONFLICT")

class InvalidCredentialsError(UnauthorizedError):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message=message)
        self.error_code = "INVALID_CREDENTIALS"

class InvalidTokenError(UnauthorizedError):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message)
        self.error_code = "INVALID_TOKEN"

class UserInactiveError(ForbiddenError):
    def __init__(self, message: str = "User account is inactive or not verified"):
        super().__init__(message=message)
        self.error_code = "USER_INACTIVE"

class EmailAlreadyExistsError(ConflictError):
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message=message)
        self.error_code = "EMAIL_ALREADY_EXISTS"

class EmailAlreadyVerifiedError(BadRequestError):
    def __init__(self, message: str = "Email is already verified"):
        super().__init__(message=message)
        self.error_code = "EMAIL_ALREADY_VERIFIED"

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    timestamp: str
    path: str | None = None

def setup_exception_handlers(app: FastAPI):
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(f"[{exc.error_code}] {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                timestamp=datetime.now(UTC).isoformat(),
                path=str(request.url.path),
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                timestamp=datetime.now(UTC).isoformat(),
                path=str(request.url.path),
            ).model_dump(),
        )
    @app.exception_handler(IntegrityError)
    async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning(f"DB Integrity Error at {request.url.path}: {str(exc.orig)}")
        
        return JSONResponse(
            status_code=409, 
            content=ErrorResponse(
                error_code="DATABASE_CONFLICT",
                message="Data conflict occurred. This record might already exist.",
                timestamp=datetime.now(UTC).isoformat(),
                path=str(request.url.path),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled: {request.method} {request.url.path}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                timestamp=datetime.now(UTC).isoformat(),
                path=str(request.url.path),
            ).model_dump(),
        )