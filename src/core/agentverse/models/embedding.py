from typing import Dict, Any, List, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import numpy as np
import logging

from src.core.agentverse.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class EmbeddingMetadata(BaseModel):
    """Metadata for embedding results"""
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        extra="allow"
    )

class EmbeddingResult(BaseModel):
    """Result from embedding search"""
    content: str
    metadata: EmbeddingMetadata = Field(default_factory=EmbeddingMetadata)
    score: float
    embedding: Optional[List[float]] = None
    distance: Optional[float] = None
    rank: Optional[int] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            np.ndarray: lambda x: x.tolist(),
            datetime: lambda dt: dt.isoformat()
        }
    )
    
    @classmethod
    def from_vector(
        cls,
        content: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        score: Optional[float] = None
    ) -> "EmbeddingResult":
        """Create result from vector
        
        Args:
            content: Text content
            vector: Embedding vector
            metadata: Optional metadata
            score: Optional similarity score
            
        Returns:
            Embedding result
            
        Raises:
            EmbeddingError: If creation fails
        """
        try:
            return cls(
                content=content,
                embedding=vector,
                metadata=EmbeddingMetadata(**(metadata or {})),
                score=score or 0.0
            )
        except Exception as e:
            logger.error(f"Failed to create embedding result: {str(e)}")
            raise EmbeddingError(
                message=f"Failed to create embedding result: {str(e)}",
                details={
                    "content_length": len(content),
                    "vector_size": len(vector) if vector else None
                }
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        data = {
            "content": self.content,
            "metadata": self.metadata.model_dump(),
            "score": self.score
        }
        
        if self.embedding is not None:
            data["embedding"] = (
                self.embedding.tolist()
                if isinstance(self.embedding, np.ndarray)
                else self.embedding
            )
        
        if self.distance is not None:
            data["distance"] = float(self.distance)
            
        if self.rank is not None:
            data["rank"] = self.rank
            
        return data
    
    def update_score(
        self,
        score: float,
        distance: Optional[float] = None,
        rank: Optional[int] = None
    ) -> None:
        """Update result scores
        
        Args:
            score: New similarity score
            distance: Optional distance value
            rank: Optional rank value
        """
        self.score = float(score)
        if distance is not None:
            self.distance = float(distance)
        if rank is not None:
            self.rank = int(rank)
    
    def __lt__(self, other: "EmbeddingResult") -> bool:
        """Compare results by score
        
        Args:
            other: Other result to compare
            
        Returns:
            Whether this result has lower score
        """
        return self.score < other.score
    
    def __repr__(self) -> str:
        return (
            f"EmbeddingResult("
            f"score={self.score:.3f}, "
            f"distance={self.distance:.3f if self.distance else None}, "
            f"rank={self.rank}, "
            f"content='{self.content[:50]}...'"
            f")"
        ) 