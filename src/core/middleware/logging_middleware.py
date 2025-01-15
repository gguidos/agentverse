import logging
from time import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next):
        request_start_time = time()
        logger.info(f"Request: {request.method} {request.url}")

        response = await call_next(request)

        process_time = time() - request_start_time
        logger.info(f"Response: {response.status_code} Process time: {process_time:.4f} seconds")

        return response
