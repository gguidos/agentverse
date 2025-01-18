from typing import List
import logging
from chromadb.api.types import Documents, EmbeddingFunction
from src.core.infrastructure.aws.get_embedings import GetEmbeddings

logger = logging.getLogger(__name__)

class EmbeddingFunctionWrapper(EmbeddingFunction):
    def __init__(self, embeddings_client):
        self.embeddings_client = embeddings_client
        
    def __call__(self, input: Documents) -> List[List[float]]:
        """Generate embeddings for the input texts"""
        if not input:
            return []
        return self.embeddings_client.get_embeddings(input)

class EmbeddingsClient:
    def __init__(self, model: str = None, api_key: str = None):
        """Initialize embeddings client"""
        self.client = GetEmbeddings()
        logger.info("Initialized AWS embeddings client")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts"""
        try:
            return self.client.get_embeddings(texts)
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise 