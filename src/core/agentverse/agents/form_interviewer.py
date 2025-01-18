from typing import Dict, Any, Optional
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.registry import agent_registry
import logging

logger = logging.getLogger(__name__)

@agent_registry.register("form_interviewer")
class FormInterviewerAgent(BaseAgent):
    """Agent for conducting form-based interviews"""
    
    name: str = "form_interviewer"
    description: str = "Agent that conducts form-based interviews"
    version: str = "1.0.0"
    default_capabilities = ["form", "memory"]

    def __init__(
        self,
        name: str,
        llm: Any,
        memory: Optional[BaseMemory] = None,
        parser: Any = None,
        prompt_template: str = "You are a form interviewer assistant.",
        tools: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """Initialize form interviewer agent
        
        Args:
            name: Agent name
            llm: LLM service
            memory: Optional memory service
            parser: Optional parser service
            prompt_template: Prompt template
            tools: Available tools
            metadata: Additional metadata
        """
        super().__init__(
            name=name,
            llm=llm,
            memory=memory,
            parser=parser,
            prompt_template=prompt_template,
            tools=tools or {},
            metadata=metadata or {}
        )
        logger.info(f"Created form interviewer agent: {name}")

    async def initialize(self):
        """Initialize agent resources"""
        if self.memory:
            await self.memory.initialize()
        logger.info(f"Initialized {self.name} agent")

    async def process_message(self, message: str) -> str:
        """Process incoming message and return response"""
        try:
            # Get form context from memory
            context = await self.memory.get_context() if self.memory else {}
            
            # Process message with LLM
            response = await self.llm.generate_response(
                prompt=self.prompt_template,
                message=message,
                context=context
            )
            
            # Store interaction in memory
            if self.memory:
                await self.memory.add_interaction(message, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise 