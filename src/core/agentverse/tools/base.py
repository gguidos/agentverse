from typing import Dict, Any, Optional, List, ClassVar, Type
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime

class ToolResult(BaseModel):
    """Result from a tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class ToolConfig(BaseModel):
    """Configuration for tools"""
    enabled: bool = True
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # Calls per minute
    timeout: float = 30.0  # Seconds
    retry_count: int = 3
    
    model_config = {
        "extra": "allow"
    }

class BaseTool(ABC, BaseModel):
    """Base class for all tools"""
    
    name: ClassVar[str]
    description: ClassVar[str]
    version: ClassVar[str] = "1.0.0"
    parameters: ClassVar[Dict[str, Any]] = Field(default_factory=dict)
    required_permissions: ClassVar[List[str]] = Field(default_factory=list)
    config: ToolConfig = Field(default_factory=ToolConfig)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function schema for this tool"""
        required_params = [
            k for k, v in self.parameters.items() 
            if isinstance(v, dict) and v.get("required", False)
        ]
        
        # Create a clean parameters schema without 'required' in individual params
        properties = {}
        for k, v in self.parameters.items():
            param_schema = v.copy()
            param_schema.pop('required', None)
            properties[k] = param_schema
        
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_params
            }
        }
    
    def validate_permissions(self, permissions: List[str]) -> bool:
        """Check if required permissions are present"""
        return all(perm in permissions for perm in self.required_permissions)
    
    async def _pre_execute(self, **kwargs) -> None:
        """Pre-execution hooks"""
        if not self.config.enabled:
            raise ToolDisabledException(f"Tool {self.name} is disabled")
            
        if self.config.requires_auth and not kwargs.get("auth_token"):
            raise ToolAuthenticationError(f"Tool {self.name} requires authentication")
    
    async def _post_execute(self, result: ToolResult) -> ToolResult:
        """Post-execution hooks"""
        result.metadata.update({
            "tool_name": self.name,
            "tool_version": self.version,
            "timestamp": datetime.utcnow()
        })
        return result
    
    async def safe_execute(self, **kwargs) -> ToolResult:
        """Execute tool with safety checks and error handling"""
        try:
            await self._pre_execute(**kwargs)
            result = await self.execute(**kwargs)
            return await self._post_execute(result)
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e),
                metadata={
                    "tool_name": self.name,
                    "tool_version": self.version,
                    "error_type": e.__class__.__name__
                }
            )
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Convert tool to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self.parameters,
            "required_permissions": self.required_permissions,
            "config": self.config.dict(),
            "schema": self.get_schema()
        }

class ToolDisabledException(Exception):
    """Raised when attempting to use a disabled tool"""
    pass

class ToolAuthenticationError(Exception):
    """Raised when tool authentication fails"""
    pass

class ToolExecutionError(Exception):
    """Raised when tool execution fails"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error 