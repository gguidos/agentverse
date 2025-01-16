from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
from src.core.agentverse.memory.manipulators.registry import manipulator_registry
from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from pydantic import Field

logger = logging.getLogger(__name__)

IMPORTANCE_PROMPT = """On the scale of 1 to 10, where 1 is purely mundane 
(e.g., brushing teeth) and 10 is extremely poignant (e.g., a break up), 
rate the likely poignancy of the following memory: {}"""

IMMEDIACY_PROMPT = """On the scale of 1 to 10, where 1 requires no immediate attention
and 10 needs quick response, rate the immediacy of: {}"""

@manipulator_registry.register("reflection")
class ReflectionManipulator(BaseMemoryManipulator):
    """Handles memory reflection and insights"""
    
    llm_service: Any = Field(default=None)
    memory_store: Any = Field(default=None)
    embeddings: Any = Field(default=None)
    memory2importance: Dict = Field(default_factory=dict)
    memory2immediacy: Dict = Field(default_factory=dict)
    importance_threshold: float = Field(default=10.0)
    accumulated_importance: float = Field(default=0.0)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def __init__(self, llm_service, memory_store, **kwargs):
        super().__init__(**kwargs)
        self.llm_service = llm_service
        self.memory_store = memory_store
    
    async def should_run(self) -> bool:
        """Determine if reflection is needed"""
        messages = await self.memory_store.get_messages()
        importance_sum = 0
        for message in messages:
            if message.content not in self.memory2importance:
                score = await self._get_importance(message.content)
                self.memory2importance[message.content] = score
            importance_sum += self.memory2importance[message.content]
            
        self.accumulated_importance = importance_sum
        return importance_sum >= self.importance_threshold
    
    async def process(self) -> None:
        """Process memories and generate insights"""
        messages = await self.memory_store.get_messages()
        if not messages:
            return
            
        # Get questions about memories
        questions = await self._generate_questions(messages)
        
        # Get relevant memories for each question
        relevant_memories = []
        for question in questions:
            memories = await self._retrieve_relevant(question, messages)
            relevant_memories.extend(memories)
            
        # Generate insights
        self.insights = await self._generate_insights(relevant_memories)
        
        # Double threshold for next reflection
        self.importance_threshold *= 2
    
    async def get_result(self) -> Optional[Dict[str, Any]]:
        """Get reflection results"""
        if not hasattr(self, 'insights') or not self.insights:
            return None
            
        return {
            "insights": self.insights,
            "type": "reflection",
            "importance_threshold": self.importance_threshold,
            "accumulated_importance": self.accumulated_importance
        }
    
    async def _get_importance(self, content: str) -> float:
        """Rate memory importance"""
        response = await self.llm.generate_response(
            IMPORTANCE_PROMPT.format(content)
        )
        try:
            return float(response.strip()) / 10
        except:
            return 0.5
            
    async def _retrieve_relevant(self, query: str, memories: List[Dict], k: int = 5):
        """Retrieve relevant memories with NMS"""
        query_embedding = await self.embeddings.get_embedding(query)
        scores = []
        
        for memory in memories:
            relevance = cosine_similarity(
                [query_embedding], 
                [memory["embedding"]]
            )[0][0]
            
            importance = self.memory2importance.get(memory["content"], 0.5)
            recency = self._get_time_decay(memory["timestamp"])
            
            score = relevance * importance * recency
            scores.append(score)
            
        return self._apply_nms(memories, scores, k) 