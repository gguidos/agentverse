from typing import Dict, List
import yaml
from pydantic import BaseModel

from src.core.llm.registry import llm_registry
from src.core.memory.registry import memory_registry
from src.core.memory.manipulators.registry import manipulator_registry
from src.core.agents.registry import agent_registry

class TaskConfig(BaseModel):
    """Task configuration model"""
    name: str
    description: str
    agents: List[Dict]
    environment: Dict
    output_parser: Dict = {}

class TaskLoader:
    """Loads and configures tasks from YAML"""
    
    def __init__(self, 
                 llm_registry,
                 memory_registry,
                 manipulator_registry,
                 agent_registry):
        self.llm_registry = llm_registry
        self.memory_registry = memory_registry
        self.manipulator_registry = manipulator_registry
        self.agent_registry = agent_registry
        
    def load_from_yaml(self, config_path: str) -> TaskConfig:
        """Load task configuration from YAML file"""
        if not config_path.endswith(".yaml"):
            raise ValueError("Config file must be a YAML file")
            
        # Load YAML
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Configure agents
        for agent_config in config["agents"]:
            # Set up memory
            memory = self.memory_registry.get(
                agent_config.get("memory_type", "vectorstore")
            )
            
            # Set up manipulators
            manipulators = {
                name: self.manipulator_registry.get(name)
                for name in agent_config.get("manipulators", ["summary", "reflection"])
            }
            
            # Set up LLM
            llm = self.llm_registry.get(
                agent_config.get("llm_type", "gpt-4")
            )
            
            agent_config.update({
                "memory": memory,
                "manipulators": manipulators,
                "llm": llm
            })
            
        return TaskConfig(**config) 