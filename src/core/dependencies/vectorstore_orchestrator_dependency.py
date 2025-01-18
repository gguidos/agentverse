from fastapi import Depends
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.dependencies.di_container import Container

async def get_vectorstore_orchestrator() -> VectorstoreOrchestratorService:
    """Get vectorstore orchestrator instance"""
    container = Container()
    return container.vectorstore_orchestrator_service()