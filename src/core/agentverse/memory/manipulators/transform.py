from typing import Dict, Any, Optional, List, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging
import json

from src.core.agentverse.memory.manipulators.base import (
    BaseMemoryManipulator,
    ManipulatorConfig,
    ManipulationResult
)
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class TransformFormat(BaseModel):
    """Memory transformation format"""
    type: Literal["structured", "summary", "highlights", "qa", "custom"] = "structured"
    template: Optional[str] = None
    max_length: Optional[int] = None
    style: str = "concise"
    include_metadata: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class TransformConfig(ManipulatorConfig):
    """Configuration for transform manipulator"""
    format: TransformFormat = Field(default_factory=TransformFormat)
    preserve_order: bool = True
    include_timestamps: bool = True
    batch_size: int = 100
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class TransformManipulator(BaseMemoryManipulator):
    """Manipulator for transforming memory content"""
    
    def __init__(self, *args, **kwargs):
        """Initialize transform manipulator"""
        super().__init__(*args, **kwargs)
        self.config: TransformConfig = (
            self.config 
            if isinstance(self.config, TransformConfig)
            else TransformConfig(**self.config.model_dump())
        )
    
    async def manipulate_memory(
        self,
        context: Optional[str] = None,
        **kwargs
    ) -> ManipulationResult:
        """Transform memory content
        
        Args:
            context: Optional context for transformation
            **kwargs: Additional transform parameters
            
        Returns:
            Transformed memory content
            
        Raises:
            MemoryManipulationError: If transformation fails
        """
        try:
            # Validate memory
            await self._validate_memory()
            
            # Get memory content
            memories = await self.memory.get_all()
            if not memories:
                return ManipulationResult(content="")
            
            # Transform content
            transformed = await self._transform_content(
                memories=memories,
                context=context,
                **kwargs
            )
            
            # Format result
            result = ManipulationResult(
                content=transformed,
                metadata={
                    "format": self.config.format.model_dump(),
                    "original_count": len(memories),
                    "context": context
                }
            )
            
            # Validate result
            await self._validate_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Memory transformation failed: {str(e)}")
            raise MemoryManipulationError(
                message=f"Failed to transform memory: {str(e)}",
                details={
                    "format": self.config.format.model_dump(),
                    "context": context
                }
            )
    
    async def _transform_content(
        self,
        memories: List[Dict[str, Any]],
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Transform memory content
        
        Args:
            memories: List of memories
            context: Optional context
            **kwargs: Additional parameters
            
        Returns:
            Transformed content
        """
        format_type = self.config.format.type
        
        if format_type == "structured":
            return await self._transform_structured(memories)
        elif format_type == "summary":
            return await self._transform_summary(memories, context)
        elif format_type == "highlights":
            return await self._transform_highlights(memories)
        elif format_type == "qa":
            return await self._transform_qa(memories, context)
        elif format_type == "custom":
            return await self._transform_custom(memories, context)
        else:
            raise MemoryManipulationError(
                message=f"Unknown format type: {format_type}"
            )
    
    async def _transform_structured(
        self,
        memories: List[Dict[str, Any]]
    ) -> str:
        """Transform to structured format
        
        Args:
            memories: List of memories
            
        Returns:
            Structured content
        """
        structured = []
        
        for i, mem in enumerate(memories, 1):
            entry = {
                "id": i,
                "content": str(mem.get("content", "")),
            }
            
            if self.config.format.include_metadata:
                entry.update({
                    k: v for k, v in mem.items()
                    if k != "content"
                })
            
            if self.config.include_timestamps:
                entry["timestamp"] = mem.get(
                    "timestamp",
                    datetime.utcnow()
                ).isoformat()
            
            structured.append(entry)
        
        return json.dumps(
            structured,
            indent=2,
            ensure_ascii=False
        )
    
    async def _transform_summary(
        self,
        memories: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> str:
        """Transform to summary format
        
        Args:
            memories: List of memories
            context: Optional context
            
        Returns:
            Summarized content
        """
        # Combine memory content
        combined = "\n".join(
            str(mem.get("content", ""))
            for mem in memories
        )
        
        # Generate summary prompt
        prompt = f"""
        Summarize the following content in a {self.config.format.style} style:
        
        {combined}
        
        Context: {context or 'None provided'}
        """
        
        # Get summary from LLM
        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=self.config.format.max_length or 500
        )
        
        return response.strip()
    
    async def _transform_highlights(
        self,
        memories: List[Dict[str, Any]]
    ) -> str:
        """Transform to highlights format
        
        Args:
            memories: List of memories
            
        Returns:
            Highlighted content
        """
        highlights = []
        
        for mem in memories:
            content = str(mem.get("content", ""))
            timestamp = mem.get("timestamp", datetime.utcnow())
            
            if self.config.include_timestamps:
                highlights.append(
                    f"[{timestamp.isoformat()}] {content}"
                )
            else:
                highlights.append(f"• {content}")
        
        return "\n\n".join(highlights)
    
    async def _transform_qa(
        self,
        memories: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> str:
        """Transform to Q&A format
        
        Args:
            memories: List of memories
            context: Optional context
            
        Returns:
            Q&A formatted content
        """
        # Combine memory content
        combined = "\n".join(
            str(mem.get("content", ""))
            for mem in memories
        )
        
        # Generate QA prompt
        prompt = f"""
        Generate a Q&A summary of the following content:
        
        {combined}
        
        Context: {context or 'None provided'}
        Style: {self.config.format.style}
        """
        
        # Get QA from LLM
        response = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=self.config.format.max_length or 1000
        )
        
        return response.strip()
    
    async def _transform_custom(
        self,
        memories: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> str:
        """Transform using custom template
        
        Args:
            memories: List of memories
            context: Optional context
            
        Returns:
            Custom formatted content
        """
        if not self.config.format.template:
            raise MemoryManipulationError(
                message="No template provided for custom format"
            )
        
        try:
            from string import Template
            template = Template(self.config.format.template)
            
            # Prepare template variables
            variables = {
                "context": context or "",
                "memory_count": len(memories),
                "current_time": datetime.utcnow().isoformat()
            }
            
            # Add memory content
            for i, mem in enumerate(memories, 1):
                variables[f"content_{i}"] = str(mem.get("content", ""))
                if self.config.include_timestamps:
                    variables[f"timestamp_{i}"] = mem.get(
                        "timestamp",
                        datetime.utcnow()
                    ).isoformat()
            
            return template.safe_substitute(variables)
            
        except Exception as e:
            raise MemoryManipulationError(
                message=f"Custom template failed: {str(e)}"
            ) 