from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.types import ASGIApp
import json

class ResponseFormatMiddleware(BaseHTTPMiddleware):
    """
    Middleware to standardize the format of API responses.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        try:
            # Process the request and get the response
            response = await call_next(request)
        except (StarletteHTTPException, FastAPIHTTPException) as exc:
            # If an HTTPException is raised, handle it separately
            standardized_response = {
                "status": "error",
                "data": None,
                "message": exc.detail,
                "error": {"code": exc.status_code, "detail": exc.detail}
            }
            return JSONResponse(content=standardized_response, status_code=exc.status_code)
        except Exception as exc:
            # Handle any unexpected exceptions
            standardized_response = {
                "status": "error",
                "data": None,
                "message": "An unexpected error occurred.",
                "error": {"detail": str(exc)}
            }
            return JSONResponse(content=standardized_response, status_code=500)

        # Check if the response is a StreamingResponse or does not contain a body
        if isinstance(response, Response) and hasattr(response, "body_iterator"):
            # Read the response body
            body = b"".join([chunk async for chunk in response.body_iterator])
            response.body_iterator = iter([body])  # Set the body iterator back

            # Load the response body as JSON if applicable
            try:
                body_data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                body_data = None
        else:
            # For other response types, retrieve the body directly
            body_data = response.body

        # Standardize the response format
        standardized_response = {
            "status": "success" if response.status_code < 400 else "error",
            "data": body_data if response.status_code < 400 else None,
            "message": "Operation completed successfully" if response.status_code < 400 else "An error occurred",
            "error": body_data if response.status_code >= 400 else None
        }

        # Return the new formatted JSON response
        return JSONResponse(content=standardized_response, status_code=response.status_code)
