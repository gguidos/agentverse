from fastapi import Depends
from src.core.services.vectorstore_service import VectorstoreService
from src.core.dependencies.di_container import Container

async def get_vectorstore_service() -> VectorstoreService:
    """Get vectorstore orchestrator instance"""
    container = Container()
    return container.vectorstore_service()