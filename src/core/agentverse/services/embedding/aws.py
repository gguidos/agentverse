from typing import List, Optional
from functools import lru_cache
import logging

from src.core.agentverse.services.embedding.base import (
    BaseEmbeddingService,
    EmbeddingConfig
)
from src.core.agentverse.exceptions import EmbeddingError
from src.core.infrastructure.aws.get_embeddings import GetEmbeddings

logger = logging.getLogger(__name__)

class AWSEmbeddingService(BaseEmbeddingService):
    """AWS Bedrock embedding service"""
    
    def _initialize(self) -> None:
        """Initialize AWS embedding service"""
        try:
            self.client = GetEmbeddings().get_embedding_function()
            logger.info(
                f"Initialized AWS embedding service "
                f"with model {self.config.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS embedding service: {str(e)}")
            raise EmbeddingError(
                message=f"AWS embedding initialization failed: {str(e)}",
                details={"model": self.config.model_name}
            )

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding using AWS Bedrock
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If embedding fails
        """
        try:
            return self.client.embed_query(text)
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            raise EmbeddingError(
                message=f"Failed to get embedding: {str(e)}",
                details={"text_length": len(text)}
            )
            
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts
        
        Args:
            texts: Texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding fails
        """
        try:
            return [
                await self.get_embedding(text)
                for text in texts
            ]
        except Exception as e:
            logger.error(f"Batch embedding failed: {str(e)}")
            raise EmbeddingError(
                message=f"Failed to get embeddings: {str(e)}",
                details={"text_count": len(texts)}
            )

@lru_cache()
def get_embeddings_service(
    config: Optional[EmbeddingConfig] = None
) -> AWSEmbeddingService:
    """Get or create singleton embedding service
    
    Args:
        config: Optional service configuration
        
    Returns:
        Embedding service instance
    """
    return AWSEmbeddingService(config) 