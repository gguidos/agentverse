from fastapi import APIRouter
from src.core.dependencies.di_container import Container  # Import the DI container
from starlette.responses import JSONResponse

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    This endpoint returns 200 OK if the service is healthy.
    """
    return JSONResponse(status_code=200, content={"status": "Healthy", "message": "Service is up and running."})

@router.get("/readiness", tags=["Readiness"])
async def readiness_check():
    """
    Advanced readiness check endpoint.
    This endpoint checks if the service is ready to accept requests by verifying dependencies.
    """
    container = Container()
    mongo_client = container.mongo_client()

    # Check if the MongoDB client is connected
    if mongo_client.client is None:
        return JSONResponse(status_code=503, content={"status": "Not Ready", "message": "MongoDB client is not connected."})

    return JSONResponse(status_code=200, content={"status": "Ready", "message": "Service is ready to accept traffic."})
