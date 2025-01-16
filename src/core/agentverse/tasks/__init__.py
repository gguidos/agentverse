"""
AgentVerse Tasks Module

This module provides task definitions and configurations for multi-agent interactions.
Tasks define how agents collaborate, their roles, and the environment they operate in.
Task configurations are typically loaded from YAML files.

Key Components:
    - Task Definitions: YAML configurations for different types of tasks
    - Task Loading: Utilities for loading and validating task configurations
    - Task Types:
        - Chat Tasks: Multi-agent collaborative conversations
        - Workflow Tasks: Sequential or parallel agent workflows
        - Custom Tasks: User-defined task configurations

Example Usage:
    >>> from src.core.agentverse.tasks import load_task, TaskConfig
    >>> 
    >>> # Load a task configuration
    >>> task = load_task("chat_task.yaml")
    >>> 
    >>> # Access task components
    >>> agents = task.agents
    >>> environment = task.environment
    >>> evaluation = task.evaluation
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Configuration for an agent in a task"""
    name: str
    type: str
    role: str
    memory: Dict[str, Any] = Field(default_factory=dict)
    llm: Dict[str, Any] = Field(default_factory=dict)
    parser: Optional[Dict[str, Any]] = None
    manipulators: List[str] = Field(default_factory=list)

class EnvironmentConfig(BaseModel):
    """Configuration for task environment"""
    type: str
    max_rounds: int = 10
    turn_taking: str = "sequential"

class EvaluationConfig(BaseModel):
    """Configuration for task evaluation"""
    type: str
    metrics: List[str]
    thresholds: Dict[str, float]

class TaskConfig(BaseModel):
    """Complete task configuration"""
    name: str
    description: str
    agents: List[AgentConfig]
    environment: EnvironmentConfig
    output_parser: Dict[str, Any]
    evaluation: EvaluationConfig

def load_task(
    task_path: str,
    base_path: Optional[str] = None
) -> TaskConfig:
    """Load task configuration from YAML file
    
    Args:
        task_path: Path to task YAML file
        base_path: Optional base path for relative paths
        
    Returns:
        Parsed task configuration
        
    Raises:
        ValueError: If task file is invalid
    """
    try:
        # Resolve path
        if base_path:
            full_path = Path(base_path) / task_path
        else:
            full_path = Path(task_path)
            
        # Load YAML
        with open(full_path) as f:
            config = yaml.safe_load(f)
            
        # Parse config
        task_config = TaskConfig(**config)
        logger.info(f"Loaded task configuration: {task_config.name}")
        
        return task_config
        
    except Exception as e:
        logger.error(f"Failed to load task configuration: {str(e)}")
        raise ValueError(f"Invalid task configuration: {str(e)}")

__all__ = [
    "TaskConfig",
    "AgentConfig", 
    "EnvironmentConfig",
    "EvaluationConfig",
    "load_task"
] 