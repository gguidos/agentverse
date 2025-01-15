# src/dependencies/api_key_dependency.py

from fastapi import HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from dependency_injector.wiring import Provide, inject
from src.core.dependencies.di_container import Container

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

@inject
async def get_api_key(
    api_key_header: str = Security(api_key_header),
    container: Container = Depends(Provide[Container.config])  # Inject configuration from the container
) -> str:
    """
    Validate the API key from the request header.
    Skip validation if in development environment.
    """
    if container.environment() == "development":
        return None  # Skip validation in development environment

    if api_key_header == container.api_key():
        return api_key_header
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )