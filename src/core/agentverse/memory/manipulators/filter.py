from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timedelta
import logging
import re

from src.core.agentverse.memory.manipulators.base import (
    BaseMemoryManipulator,
    ManipulatorConfig,
    ManipulationResult
)
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class FilterCriteria(BaseModel):
    """Filter criteria configuration"""
    relevance: float = Field(ge=0.0, le=1.0, default=0.5)
    recency: Optional[timedelta] = Field(default=timedelta(days=7))
    topics: List[str] = Field(default_factory=list)
    min_length: int = Field(ge=0, default=0)
    max_length: int = Field(ge=0, default=1000)
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class FilterConfig(ManipulatorConfig):
    """Configuration for filter manipulator"""
    criteria: FilterCriteria = Field(default_factory=FilterCriteria)
    preserve_order: bool = True
    case_sensitive: bool = False
    batch_size: int = 100
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class FilterManipulator(BaseMemoryManipulator):
    """Manipulator for filtering memory content"""
    
    def __init__(self, *args, **kwargs):
        """Initialize filter manipulator"""
        super().__init__(*args, **kwargs)
        self.config: FilterConfig = (
            self.config 
            if isinstance(self.config, FilterConfig)
            else FilterConfig(**self.config.model_dump())
        )
    
    async def manipulate_memory(
        self,
        context: Optional[str] = None,
        **kwargs
    ) -> ManipulationResult:
        """Filter memory content
        
        Args:
            context: Optional context for filtering
            **kwargs: Additional filter parameters
            
        Returns:
            Filtered memory content
            
        Raises:
            MemoryManipulationError: If filtering fails
        """
        try:
            # Validate memory
            await self._validate_memory()
            
            # Get memory content
            memories = await self.memory.get_all()
            if not memories:
                return ManipulationResult(content="")
            
            # Apply filters
            filtered = await self._apply_filters(
                memories=memories,
                context=context,
                **kwargs
            )
            
            # Format result
            result = ManipulationResult(
                content=self._format_content(filtered),
                metadata={
                    "original_count": len(memories),
                    "filtered_count": len(filtered),
                    "criteria": self.config.criteria.model_dump(),
                    "context": context
                }
            )
            
            # Validate result
            await self._validate_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Memory filtering failed: {str(e)}")
            raise MemoryManipulationError(
                message=f"Failed to filter memory: {str(e)}",
                details={
                    "context": context,
                    "criteria": self.config.criteria.model_dump()
                }
            )
    
    async def _apply_filters(
        self,
        memories: List[Dict[str, Any]],
        context: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Apply filter criteria
        
        Args:
            memories: List of memories
            context: Optional context
            **kwargs: Additional criteria
            
        Returns:
            Filtered memories
        """
        filtered = memories.copy()
        
        # Apply relevance filter
        if context and self.config.criteria.relevance > 0:
            relevance_scores = await self._calculate_relevance(
                memories=filtered,
                context=context
            )
            filtered = [
                mem for mem, score in zip(filtered, relevance_scores)
                if score >= self.config.criteria.relevance
            ]
        
        # Apply recency filter
        if self.config.criteria.recency:
            cutoff = datetime.utcnow() - self.config.criteria.recency
            filtered = [
                mem for mem in filtered
                if mem.get("timestamp", datetime.utcnow()) >= cutoff
            ]
        
        # Apply topic filter
        if self.config.criteria.topics:
            filtered = await self._filter_by_topics(filtered)
        
        # Apply length filters
        filtered = [
            mem for mem in filtered
            if (
                len(str(mem.get("content", ""))) >= 
                self.config.criteria.min_length
                and
                (
                    self.config.criteria.max_length == 0
                    or len(str(mem.get("content", ""))) <= 
                    self.config.criteria.max_length
                )
            )
        ]
        
        # Apply pattern filters
        filtered = await self._filter_by_patterns(filtered)
        
        # Preserve order if configured
        if self.config.preserve_order:
            filtered.sort(
                key=lambda x: memories.index(x)
            )
        
        return filtered
    
    async def _calculate_relevance(
        self,
        memories: List[Dict[str, Any]],
        context: str
    ) -> List[float]:
        """Calculate relevance scores
        
        Args:
            memories: List of memories
            context: Context for relevance
            
        Returns:
            List of relevance scores
        """
        try:
            # Get embeddings
            context_embedding = await self.llm_service.get_embedding(context)
            
            memory_contents = [
                str(mem.get("content", "")) for mem in memories
            ]
            memory_embeddings = await self.llm_service.get_embeddings(
                memory_contents
            )
            
            # Calculate cosine similarity
            import numpy as np
            scores = [
                float(np.dot(context_embedding, mem_emb))
                for mem_emb in memory_embeddings
            ]
            
            return scores
            
        except Exception as e:
            logger.error(f"Relevance calculation failed: {str(e)}")
            return [1.0] * len(memories)  # Default to keep all
    
    async def _filter_by_topics(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter by topics
        
        Args:
            memories: List of memories
            
        Returns:
            Filtered memories
        """
        if not self.config.criteria.topics:
            return memories
            
        filtered = []
        topics = [
            t.lower() if not self.config.case_sensitive else t
            for t in self.config.criteria.topics
        ]
        
        for mem in memories:
            content = str(mem.get("content", ""))
            if not self.config.case_sensitive:
                content = content.lower()
                
            if any(topic in content for topic in topics):
                filtered.append(mem)
                
        return filtered
    
    async def _filter_by_patterns(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter by patterns
        
        Args:
            memories: List of memories
            
        Returns:
            Filtered memories
        """
        filtered = memories
        
        # Apply exclude patterns
        for pattern in self.config.criteria.exclude_patterns:
            try:
                regex = re.compile(
                    pattern,
                    flags=re.IGNORECASE if not self.config.case_sensitive else 0
                )
                filtered = [
                    mem for mem in filtered
                    if not regex.search(str(mem.get("content", "")))
                ]
            except Exception as e:
                logger.warning(f"Invalid exclude pattern '{pattern}': {str(e)}")
        
        # Apply include patterns
        for pattern in self.config.criteria.include_patterns:
            try:
                regex = re.compile(
                    pattern,
                    flags=re.IGNORECASE if not self.config.case_sensitive else 0
                )
                filtered = [
                    mem for mem in filtered
                    if regex.search(str(mem.get("content", "")))
                ]
            except Exception as e:
                logger.warning(f"Invalid include pattern '{pattern}': {str(e)}")
        
        return filtered
    
    def _format_content(
        self,
        memories: List[Dict[str, Any]]
    ) -> str:
        """Format filtered content
        
        Args:
            memories: Filtered memories
            
        Returns:
            Formatted content string
        """
        return "\n\n".join(
            str(mem.get("content", ""))
            for mem in memories
        ) 