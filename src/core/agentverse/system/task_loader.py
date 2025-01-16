"""
Task loader implementation
"""

import logging
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel

from src.core.agentverse.exceptions import ConfigError

logger = logging.getLogger(__name__)

class TaskConfig(BaseModel):
    """Task configuration"""
    name: str
    description: Optional[str] = None
    agents: list
    environment: Dict[str, Any]
    tools: Optional[list] = None
    resources: Optional[Dict[str, Any]] = None

class TaskLoader:
    """Loader for task configurations"""
    
    @staticmethod
    async def load_task(path: str) -> TaskConfig:
        """Load task configuration from YAML file
        
        Args:
            path: Path to YAML file
            
        Returns:
            Task configuration
            
        Raises:
            ConfigError: If loading fails
        """
        try:
            # Load YAML file
            with open(path, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            # Validate and create config
            config = TaskConfig(**config_dict)
            logger.info(f"Loaded task config: {config.name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load task config: {e}")
            raise ConfigError(
                message="Task config loading failed",
                details={
                    "path": path,
                    "error": str(e)
                }
            )
    
    @staticmethod
    async def validate_config(config: Dict[str, Any]) -> None:
        """Validate task configuration
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigError: If validation fails
        """
        try:
            TaskConfig(**config)
        except Exception as e:
            raise ConfigError(
                message="Invalid task configuration",
                details={"error": str(e)}
            ) 