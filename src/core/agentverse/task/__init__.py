"""Task Module"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from src.core.agentverse.config import load_config
from src.core.agentverse.initialization import (
    load_agent_config,
    load_environment_config
)
from src.core.agentverse.exceptions import TaskError

logger = logging.getLogger(__name__)

class TaskConfig:
    """Task configuration"""
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "default")
        self.description = kwargs.get("description", "")
        self.environment = kwargs.get("environment", {})
        self.agents = kwargs.get("agents", [])

class Task:
    """Task controller"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize task"""
        self.config = TaskConfig(**config)
        self.environment = None
        self.agents = []
        
        # Load components
        self._load_components()
    
    def _load_components(self):
        """Load task components"""
        try:
            # Load environment
            self.environment = load_environment_config(self.config.environment)
            
            # Load agents
            for agent_config in self.config.agents:
                agent = load_agent_config(agent_config)
                self.agents.append(agent)
                
        except Exception as e:
            logger.error(f"Failed to load components: {str(e)}")
            raise TaskError(f"Failed to load components: {str(e)}") 