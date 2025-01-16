from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class EmbeddingConfig(BaseModel):
    """Configuration for embedding service"""
    model_name: str
    dimension: int
    cache_size: int = 1000
    normalize: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseEmbeddingService(ABC):
    """Base class for embedding services"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig(
            model_name="default",
            dimension=1024
        )
        self._initialize()
        
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize embedding service"""
        pass
        
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        pass
        
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts
        
        Args:
            texts: Texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass 