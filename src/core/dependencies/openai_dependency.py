from fastapi import Depends
from dependency_injector.wiring import inject, Provide
from src.core.repositories.di_container import Container
from src.core.services.openai_service import OpenAIService

@inject
async def get_openai_service(
    container: Container = Depends(Provide[Container])
) -> OpenAIService:
    """Dependency provider for OpenAIService"""
    return OpenAIService(
        api_key=container.config.openai_api_key(),
        system_prompt=container.config.system_prompt()
    ) 