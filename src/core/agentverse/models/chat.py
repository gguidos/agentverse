from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import json
import logging

from src.core.agentverse.message.base import Message, AgentAction
from src.core.agentverse.exceptions import SerializationError

logger = logging.getLogger(__name__)

class ChatMetadata(BaseModel):
    """Metadata for chat messages"""
    source: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    priority: int = 0
    
    model_config = ConfigDict(
        extra="allow"
    )

class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    content: str
    metadata: Optional[ChatMetadata] = None
    context: Optional[Dict[str, Any]] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    timeout: Optional[float] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )
    
    def to_message(self) -> Message:
        """Convert request to message
        
        Returns:
            Message instance
        """
        return Message(
            content=self.content,
            sender=self.sender,
            receiver={self.receiver} if self.receiver else None,
            metadata={
                **(self.metadata.model_dump() if self.metadata else {}),
                "context": self.context or {},
                "timeout": self.timeout
            }
        )

class ToolUsage(BaseModel):
    """Model for tool usage information"""
    tool: str
    input: Dict[str, Any]
    output: Optional[Any] = None
    status: str
    duration: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    @classmethod
    def from_action(cls, action: AgentAction) -> "ToolUsage":
        """Create from agent action
        
        Args:
            action: Source action
            
        Returns:
            Tool usage instance
        """
        return cls(
            tool=action.tool,
            input=action.input,
            output=action.output,
            status=action.status,
            duration=action.duration,
            error=action.error,
            timestamp=action.timestamp
        )

class ChatResponse(BaseModel):
    """Response model for chat interactions"""
    response: str
    task_id: str
    tool_usage: Optional[Dict[str, List[ToolUsage]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            ToolUsage: lambda t: t.model_dump()
        }
    )
    
    @classmethod
    def from_message(
        cls,
        message: Message,
        task_id: str
    ) -> "ChatResponse":
        """Create from message
        
        Args:
            message: Source message
            task_id: Task identifier
            
        Returns:
            Chat response instance
        """
        # Group tool usage by tool name
        tool_usage = {}
        for action in message.actions:
            usage = ToolUsage.from_action(action)
            tool_usage.setdefault(action.tool, []).append(usage)
        
        return cls(
            response=message.content,
            task_id=task_id,
            tool_usage=tool_usage or None,
            metadata=message.metadata,
            timestamp=message.timestamp
        )
    
    def model_dump(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Custom serialization
        
        Returns:
            Serialized response
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            data = {
                "response": self.response,
                "task_id": self.task_id,
                "timestamp": self.timestamp.isoformat(),
                "metadata": self._serialize_metadata()
            }
            
            if self.tool_usage:
                data["tool_usage"] = {
                    tool: [
                        usage.model_dump()
                        for usage in usages
                    ]
                    for tool, usages in self.tool_usage.items()
                }
            
            return data
            
        except Exception as e:
            logger.error(f"Response serialization failed: {str(e)}")
            raise SerializationError(
                message=f"Failed to serialize response: {str(e)}",
                details={
                    "task_id": self.task_id,
                    "tools": list(self.tool_usage.keys()) if self.tool_usage else None
                }
            )
    
    def _serialize_metadata(self) -> Optional[Dict[str, Any]]:
        """Safely serialize metadata
        
        Returns:
            Serialized metadata
        """
        if not self.metadata:
            return None
            
        def _serialize_value(value: Any) -> Any:
            """Recursively serialize value"""
            if isinstance(value, (str, int, float, bool, type(None))):
                return value
            if isinstance(value, (list, tuple, set)):
                return [_serialize_value(v) for v in value]
            if isinstance(value, dict):
                return {
                    str(k): _serialize_value(v)
                    for k, v in value.items()
                }
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        
        return {
            str(k): _serialize_value(v)
            for k, v in self.metadata.items()
        } 