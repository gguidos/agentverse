from typing import Dict, Any, Optional, ClassVar
from pydantic import BaseModel, Field
from datetime import datetime

class ToolResult(BaseModel):
    """Result from a tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ToolConfig(BaseModel):
    """Base configuration for tools"""
    enabled: bool = True
    timeout: float = 30.0  # Seconds

# Tool-related exceptions
class ToolError(Exception):
    """Base class for tool-related errors"""
    pass

class ToolExecutionError(ToolError):
    """Raised when tool execution fails"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error

class ToolAuthenticationError(ToolError):
    """Raised when tool authentication fails"""
    pass

class ToolPermissionError(ToolError):
    """Raised when tool lacks required permissions"""
    pass

class ToolValidationError(ToolError):
    """Raised when tool input validation fails"""
    pass

class ToolDependencyError(ToolError):
    """Raised when tool dependencies are missing or invalid"""
    pass

class BaseTool:
    """Base class for all tools"""
    
    # Class-level metadata
    name: ClassVar[str] = "base_tool"
    description: ClassVar[str] = "Base tool description"
    version: ClassVar[str] = "1.0.0"
    required_permissions: ClassVar[list] = []
    parameters: ClassVar[Dict[str, Any]] = {}
    
    def __init__(self, config: Optional[ToolConfig] = None, **kwargs):
        self.config = config or ToolConfig()
        self._validate_dependencies(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def _validate_dependencies(self, dependencies: Dict[str, Any]):
        """Validate tool dependencies"""
        pass
        
    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get tool metadata"""
        return {
            "name": cls.name,
            "description": cls.description,
            "version": cls.version,
            "permissions": cls.required_permissions,
            "parameters": cls.parameters
        }

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Tool must implement execute method") 