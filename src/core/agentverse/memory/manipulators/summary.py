from typing import List, Dict, Optional, Any
from pydantic import Field, validator
import re
from string import Template
import logging

from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from src.core.agentverse.memory.manipulators.registry import manipulator_registry

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_TEMPLATE = """Previous summary:
${summary}

New messages:
${new_lines}

Please provide a concise summary incorporating both the previous summary and new messages.
Focus on key points and maintain continuity.
"""

@manipulator_registry.register("summary")
class SummaryManipulator(BaseMemoryManipulator):
    """Manipulator that maintains a running summary using LLM"""
    
    llm_service: Any = Field(default=None)
    memory_store: Any = Field(default=None)
    buffer: str = Field(default="")
    prompt_template: str = Field(default=DEFAULT_SUMMARY_TEMPLATE)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def __init__(self, llm_service, memory_store, **kwargs):
        super().__init__(**kwargs)
        self.llm_service = llm_service
        self.memory_store = memory_store
    
    async def should_run(self) -> bool:
        """Determine if summary should be generated"""
        messages = await self.memory_store.get_messages()
        return len(messages) > 0
    
    async def process(self) -> None:
        """Generate summary of recent messages"""
        try:
            messages = await self.memory_store.get_messages()
            if not messages:
                return
            
            new_lines = "\n".join(m.content for m in messages)
            prompt = Template(self.prompt_template).safe_substitute({
                "summary": self.buffer,
                "new_lines": new_lines
            })
            
            response = await self.llm_service.generate_response(prompt)
            self.buffer = response
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            raise
    
    async def get_result(self) -> Optional[Dict[str, Any]]:
        """Get the generated summary"""
        if not self.buffer:
            return None
            
        return {
            "summary": self.buffer,
            "type": "summary"
        } 