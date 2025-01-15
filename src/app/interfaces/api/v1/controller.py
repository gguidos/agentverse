from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from typing import List
from src.core.dependencies.api_key_dependency import get_api_key
from src.core.dependencies.di_container import Container

# Create a FastAPI router for user-related endpoints
router = APIRouter()

# Get configuration from the container to conditionally include dependencies
container = Container()

# Conditionally add API key protection based on environment
api_key_dependency = Depends(get_api_key) if container.config.environment() != "development" else None