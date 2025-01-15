from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to extract or set a request ID for each request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract the request ID from the headers or set a default value
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Store request ID in the request state for future use
        request.state.request_id = request_id

        # Continue processing the request and get the response
        response = await call_next(request)

        # Optionally, add the request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
