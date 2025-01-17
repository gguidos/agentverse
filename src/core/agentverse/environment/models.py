"""Environment models"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class AgentConfig(BaseModel):
    """Agent-specific configuration"""
    llm_config: Dict[str, Any] = {"type": "mock"}
    capabilities: List[str] = []
    memory_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

class ToolConfig(BaseModel):
    """Tool-specific configuration"""
    enabled: bool = True
    timeout: float = 30.0
    parameters: Dict[str, Any] = {}
    permissions: List[str] = []

class StorageConfig(BaseModel):
    """Storage configuration"""
    vectorstore: Optional[Dict[str, Any]] = None
    memory_store: Optional[Dict[str, Any]] = None
    file_store: Optional[Dict[str, Any]] = None
    metadata_store: Optional[Dict[str, Any]] = None

class EnvironmentConfig(BaseModel):
    """Configuration for an environment"""
    # Core configurations
    agents: Dict[str, AgentConfig] = {}  # Map agent names to their configs
    tools: Dict[str, ToolConfig] = {}    # Map tool names to their configs
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # Environment-wide settings
    max_iterations: int = 100
    timeout: float = 300.0  # 5 minutes
    auto_recovery: bool = True
    logging_level: str = "INFO"
    
    # Integration configs
    llm_config: Optional[Dict[str, Any]] = None  # Default LLM config
    api_keys: Dict[str, str] = {}
    external_services: Dict[str, Dict[str, Any]] = {}

class Environment(BaseModel):
    """Environment model"""
    id: str
    name: str
    description: str
    type: str = "default"  # e.g., "chat", "task", "simulation"
    config: EnvironmentConfig
    enabled_capabilities: List[str]
    metadata: Dict[str, Any] = {}
    status: str = "inactive"  # inactive, active, error
    created_at: datetime
    updated_at: Optional[datetime] = None

class EnvironmentStepResult(BaseModel):
    """Result of an environment step"""
    output: str
    logs: List[str] = []
    metrics: Dict[str, Any] = {}
    done: bool = False
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# For backwards compatibility
__all__ = [
    'AgentConfig',
    'ToolConfig',
    'StorageConfig',
    'EnvironmentConfig',
    'Environment',
    'EnvironmentStepResult'
] 