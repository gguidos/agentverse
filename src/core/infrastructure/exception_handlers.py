from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging

# Create a logger instance
logger = logging.getLogger(__name__)

def register_exception_handlers(app):
    """
    Register global exception handlers for the FastAPI app.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTPException: {exc.detail}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "data": None, "message": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "data": None,
                "message": "Validation error",
                "error": exc.errors(),
            },
        )
    
    @app.exception_handler(DuplicateUserException)
    async def duplicate_user_exception_handler(request: Request, exc: DuplicateUserException):
        logger.error(f"DuplicateUserException: {exc.detail}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "data": None, "message": exc.detail},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        logger.error(f"Pydantic validation error: {exc.errors()}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "data": None,
                "message": "Data validation error",
                "error": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"Starlette HTTP Exception: {exc.detail}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "data": None, "message": exc.detail},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"status": "error", "data": None, "message": "An unexpected error occurred."},
        )

class DuplicateUserException(HTTPException):
    def __init__(self, email: str):
        super().__init__(status_code=400, detail=f"User with email {email} already exists.")