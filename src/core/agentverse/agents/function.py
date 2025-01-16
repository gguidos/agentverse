"""
Function agent implementation
"""

import logging
from typing import Any, Dict, List, Optional
import inspect

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class FunctionAgent(BaseAgent):
    """Agent for executing functions"""
    
    def __init__(
        self,
        name: str,
        functions: Dict[str, callable],
        allowed_tools: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize function agent
        
        Args:
            name: Agent name
            functions: Dictionary of available functions
            allowed_tools: Optional list of allowed tool names
            **kwargs: Additional arguments
        """
        super().__init__(name=name, **kwargs)
        self.functions = functions
        self.allowed_tools = allowed_tools or list(functions.keys())
        
        # Validate functions
        for name, func in functions.items():
            if not callable(func):
                raise AgentError(
                    message=f"Invalid function: {name}",
                    details={"error": "Function must be callable"}
                )
    
    async def process_message(self, message: Message) -> Message:
        """Process incoming message
        
        Args:
            message: Input message
            
        Returns:
            Response message
            
        Raises:
            AgentError: If processing fails
        """
        try:
            # Store message in history
            self.message_history.append(message)
            
            # Extract function call from message
            func_name = message.metadata.get("function")
            if not func_name:
                raise AgentError(
                    message="Missing function name",
                    details={"message_id": message.id}
                )
            
            # Check if function is allowed
            if func_name not in self.allowed_tools:
                raise AgentError(
                    message=f"Function not allowed: {func_name}",
                    details={"allowed": self.allowed_tools}
                )
            
            # Get function
            func = self.functions.get(func_name)
            if not func:
                raise AgentError(
                    message=f"Function not found: {func_name}",
                    details={"available": list(self.functions.keys())}
                )
            
            # Get function arguments
            args = message.metadata.get("args", [])
            kwargs = message.metadata.get("kwargs", {})
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Create response message
            response = Message(
                content=str(result),
                type=MessageType.FUNCTION,
                role=MessageRole.FUNCTION,
                sender_id=self.name,
                receiver_id=message.sender_id,
                parent_id=message.id,
                metadata={
                    "function": func_name,
                    "args": args,
                    "kwargs": kwargs,
                    "result_type": type(result).__name__
                }
            )
            
            # Store response
            self.message_history.append(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise AgentError(
                message="Function execution failed",
                details={
                    "agent": self.name,
                    "error": str(e)
                }
            )
    
    async def get_function_info(self, func_name: str) -> Dict[str, Any]:
        """Get function information
        
        Args:
            func_name: Name of function
            
        Returns:
            Function information dictionary
            
        Raises:
            AgentError: If function not found
        """
        if func_name not in self.functions:
            raise AgentError(
                message=f"Function not found: {func_name}"
            )
            
        func = self.functions[func_name]
        sig = inspect.signature(func)
        
        return {
            "name": func_name,
            "doc": func.__doc__,
            "parameters": [
                {
                    "name": name,
                    "kind": str(param.kind),
                    "default": str(param.default) if param.default is not param.empty else None,
                    "annotation": str(param.annotation) if param.annotation is not param.empty else None
                }
                for name, param in sig.parameters.items()
            ]
        } 