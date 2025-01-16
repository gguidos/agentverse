from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.core.agentverse.memory.base import BaseMemory, Message
from src.core.agentverse.memory.registry import memory_registry

@memory_registry.register("generative")
class GenerativeMemory(BaseMemory):
    """Memory system with reflection and summarization"""
    
    def __init__(self, llm_service, embedding_service):
        super().__init__()
        self.llm = llm_service
        self.embeddings = embedding_service
        self.importance_scores = {}
        self.immediacy_scores = {}
        self.access_times = {}
        
    async def add_message(self, messages: List[Message]) -> None:
        """Add new messages with embeddings and scores"""
        for message in messages:
            embedding = await self.embeddings.get_embedding(message.content)
            
            # Store embedding in message metadata
            message.metadata["embedding"] = embedding
            message.metadata["last_accessed"] = datetime.now()
            
            # Score the message
            self.importance_scores[message.content] = await self._get_importance(message.content)
            self.immediacy_scores[message.content] = await self._get_immediacy(message.content)
            
            self.messages.append(message)
        
    async def get_messages(self, 
                          start: int = 0,
                          limit: int = 100,
                          filters: Dict = None) -> List[Message]:
        """Get messages with optional filtering"""
        filtered = self.messages
        if filters:
            filtered = [
                m for m in filtered 
                if all(m.dict().get(k) == v for k, v in filters.items())
            ]
        return filtered[start:start+limit]
        
    async def retrieve_relevant(self, query: str, k: int = 5) -> List[Message]:
        """Retrieve relevant messages using scoring system"""
        query_embedding = await self.embeddings.get_embedding(query)
        scores = []
        
        for message in self.messages:
            relevance = cosine_similarity(
                [query_embedding], 
                [message.metadata["embedding"]]
            )[0][0]
            
            recency = self._get_time_score(
                message.metadata["last_accessed"],
                decay_rate=0.99
            )
            
            importance = self.importance_scores[message.content] / 10
            immediacy = self.immediacy_scores[message.content] / 10
            
            score = relevance * max(
                recency * importance,
                self._get_time_score(message.timestamp, 0.90) * immediacy
            )
            scores.append(score)
            
        # Get top k messages
        top_indices = np.argsort(scores)[-k:][::-1]
        return [self.messages[i] for i in top_indices]
        
    def to_string(self) -> str:
        """Convert memory contents to string"""
        return "\n".join([
            f"{msg.sender}: {msg.content}" 
            for msg in self.messages
        ])
        
    async def reset(self) -> None:
        """Clear all memory contents"""
        self.messages = []
        self.importance_scores = {}
        self.immediacy_scores = {}
        self.access_times = {}
        
    async def _get_importance(self, content: str) -> float:
        """Rate memory importance"""
        response = await self.llm.generate_response(
            f"On scale 1-10, rate importance: {content}"
        )
        try:
            return float(response.strip()) / 10
        except:
            return 0.5
            
    async def _get_immediacy(self, content: str) -> float:
        """Rate memory immediacy"""
        response = await self.llm.generate_response(
            f"On scale 1-10, rate urgency: {content}"
        )
        try:
            return float(response.strip()) / 10
        except:
            return 0.5
            
    def _get_time_score(self, timestamp: datetime, decay_rate: float) -> float:
        """Calculate time-based decay score"""
        age = (datetime.now() - timestamp).total_seconds()
        return decay_rate ** (age / 3600)  # Decay per hour 