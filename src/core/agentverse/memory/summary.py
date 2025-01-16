from typing import List, Dict, Optional
from pydantic import Field, validator
import re
from string import Template
import logging

from src.core.agentverse.memory.base import BaseMemory, Message
from src.core.agentverse.memory.registry import memory_registry

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_TEMPLATE = """Previous summary:
${summary}

New messages:
${new_lines}

Please provide a concise summary incorporating both the previous summary and new messages.
Focus on key points and maintain continuity.
"""

@memory_registry.register("summary")
class SummaryMemory(BaseMemory):
    """Memory that maintains a running summary using LLM"""
    
    messages: List[Message] = Field(default_factory=list)
    buffer: str = Field(default="")
    recursive: bool = Field(default=False)
    prompt_template: str = Field(default=DEFAULT_SUMMARY_TEMPLATE)
    
    def __init__(self, llm_service, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = llm_service
        
    @validator("prompt_template")
    def validate_template(cls, v, values):
        """Validate prompt template contains required variables"""
        recursive = values.get("recursive", False)
        
        # Check for required template variables
        summary_exists = "${summary}" in v
        new_lines_exists = "${new_lines}" in v
        
        if recursive and not (summary_exists and new_lines_exists):
            raise ValueError(
                "Recursive summaries require both ${summary} and ${new_lines} in template"
            )
        elif not recursive and not new_lines_exists:
            raise ValueError(
                "Template must contain ${new_lines}"
            )
            
        return v
        
    async def add_message(self, messages: List[Message]) -> None:
        """Add messages and update summary"""
        self.messages.extend(messages)
        
        # Get new content to summarize
        new_lines = "\n".join(m.content for m in messages)
        
        # Update summary
        await self._update_summary(new_lines)
        
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
        
    async def _update_summary(self, new_content: str) -> None:
        """Update summary buffer with new content"""
        try:
            # Build prompt
            prompt = Template(self.prompt_template).safe_substitute({
                "summary": self.buffer,
                "new_lines": new_content
            })
            
            # Generate new summary
            response = await self.llm.generate_response(prompt)
            
            # Update buffer
            if self.recursive:
                self.buffer = response
            else:
                self.buffer = f"{self.buffer}\n{response}" if self.buffer else response
                
            logger.debug(f"Updated summary: {self.buffer[:100]}...")
            
        except Exception as e:
            logger.error(f"Failed to update summary: {str(e)}")
            raise
            
    def to_string(self, *args, **kwargs) -> str:
        """Get current summary"""
        return self.buffer
        
    async def reset(self) -> None:
        """Clear memory and summary"""
        self.messages = []
        self.buffer = "" 