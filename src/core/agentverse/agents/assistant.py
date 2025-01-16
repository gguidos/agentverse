from typing import Dict, Any, Optional, Set, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import json
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.actions import AgentAction, AgentStep, ActionSequence
from src.core.agentverse.message.base import Message
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.tools.base import BaseTool
from src.core.agentverse.registry import agent_registry
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class AssistantConfig(BaseModel):
    """Configuration for assistant agent"""
    role_description: str = "A helpful AI assistant"
    system_prompt: str = "You are a helpful AI assistant."
    max_tool_uses: int = 3
    allow_multi_tool: bool = True
    validate_outputs: bool = True
    track_tool_usage: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class AssistantState(BaseModel):
    """State for assistant agent"""
    status: str = "idle"
    current_task: Optional[str] = None
    last_active: Optional[datetime] = None
    tool_uses: Dict[str, int] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

@agent_registry.register("assistant")
class AssistantAgent(BaseAgent):
    """AI Assistant implementation"""
    
    name: ClassVar[str] = "assistant"
    description: ClassVar[str] = "General purpose AI assistant"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        memory: BaseMemory,
        config: Optional[AssistantConfig] = None,
        tools: Optional[Dict[str, BaseTool]] = None
    ):
        """Initialize assistant agent
        
        Args:
            llm_service: LLM service instance
            memory: Memory instance
            config: Optional configuration
            tools: Optional tool dictionary
        """
        super().__init__(
            llm_service=llm_service,
            memory=memory,
            config=config or AssistantConfig()
        )
        self.tools = tools or {}
        self.state = AssistantState()
        self.action_sequence = ActionSequence()
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def process_task(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process task request
        
        Args:
            task: Task dictionary
            
        Returns:
            Task result
            
        Raises:
            AgentError: If processing fails
        """
        try:
            start_time = datetime.utcnow()
            
            # Update state
            await self._update_state(
                status="processing",
                current_task=task.get("task_id")
            )
            
            # Store task in memory
            await self.memory.add(
                content=task["content"],
                metadata={
                    "task_id": task["task_id"],
                    "timestamp": start_time
                }
            )
            
            # Get tool schemas
            tool_schemas = [
                tool.get_schema()
                for tool in self.tools.values()
            ]
            
            # Create initial message
            messages = [{
                "role": "user",
                "content": task["content"]
            }]
            
            # Get initial response
            response = await self.llm.chat_completion(
                messages=messages,
                functions=tool_schemas,
                function_call="auto"
            )
            
            tool_results = []
            
            # Handle tool calls
            while (
                hasattr(response, 'function_call') and
                response.function_call and
                len(tool_results) < self.config.max_tool_uses
            ):
                # Extract tool call
                tool_name = response.function_call["name"]
                tool_args = json.loads(response.function_call["arguments"])
                
                # Create and track action
                action = AgentAction(
                    tool=tool_name,
                    input=tool_args
                )
                step = AgentStep(action=action)
                
                try:
                    # Execute tool
                    result = await self.tools[tool_name].execute(**tool_args)
                    
                    # Update action/step
                    action.complete(
                        output=result.dict(),
                        duration=step.duration
                    )
                    step.complete(result.dict())
                    
                except Exception as e:
                    action.fail(str(e))
                    step.fail(str(e))
                    logger.error(f"Tool execution failed: {str(e)}")
                
                # Track step
                self.action_sequence.add_step(step)
                
                # Update tool usage
                self.state.tool_uses[tool_name] = (
                    self.state.tool_uses.get(tool_name, 0) + 1
                )
                
                # Add to results
                tool_results.append({
                    "tool": tool_name,
                    "input": tool_args,
                    "output": action.output,
                    "error": action.metadata.error
                })
                
                # Add to conversation
                messages.extend([
                    {
                        "role": "assistant",
                        "content": None,
                        "function_call": response.function_call
                    },
                    {
                        "role": "function",
                        "name": tool_name,
                        "content": json.dumps(action.output or {})
                    }
                ])
                
                # Get next response if multi-tool allowed
                if self.config.allow_multi_tool:
                    response = await self.llm.chat_completion(
                        messages=messages,
                        functions=tool_schemas,
                        function_call="auto"
                    )
                else:
                    break
            
            # Get final response
            final_response = await self.llm.chat_completion(messages=messages)
            
            # Complete sequence
            self.action_sequence.complete()
            
            # Update state
            self.state.memory[task["task_id"]] = {
                "task": task,
                "response": final_response.content,
                "tool_results": tool_results,
                "metrics": self.action_sequence.get_metrics()
            }
            
            await self._update_state(status="idle", current_task=None)
            
            return {
                "status": "success",
                "response": final_response.content,
                "tool_results": tool_results,
                "metrics": self.action_sequence.get_metrics()
            }
            
        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}")
            await self._update_state(status="error")
            raise AgentError(
                message=f"Failed to process task: {str(e)}",
                details={
                    "task_id": task.get("task_id"),
                    "tools_used": len(tool_results) if 'tool_results' in locals() else 0
                }
            )
    
    async def _update_state(self, **kwargs) -> None:
        """Update agent state
        
        Args:
            **kwargs: State updates
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.state.last_active = datetime.utcnow()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics
        
        Returns:
            Metrics dictionary
        """
        metrics = super().get_metrics()
        
        # Add tool usage metrics
        metrics.update({
            "tool_uses": dict(self.state.tool_uses),
            "total_tool_uses": sum(self.state.tool_uses.values()),
            "unique_tools_used": len(self.state.tool_uses)
        })
        
        # Add sequence metrics if available
        if self.action_sequence:
            metrics.update(self.action_sequence.get_metrics())
            
        return metrics
    
    async def reset(self) -> None:
        """Reset agent state"""
        await super().reset()
        self.state = AssistantState()
        self.action_sequence = ActionSequence() 