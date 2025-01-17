"""Initialization module for AgentVerse"""

from typing import Dict, Any, Type
from src.core.agentverse.agents import BaseAgent, AssistantAgent, UserAgent
from src.core.agentverse.llms import create_llm, LLM_TYPES
from src.core.agentverse.environment import BaseEnvironment, ENVIRONMENT_TYPES
from src.core.agentverse.exceptions import ConfigError

def load_llm_config(config: Dict[str, Any]):
    """Load LLM from config"""
    try:
        llm_type = config.get("type")
        if not llm_type:
            raise ConfigError("LLM type not specified")
            
        return create_llm(config)
        
    except Exception as e:
        raise ConfigError(f"Failed to load LLM config: {str(e)}")

def load_agent_config(config: Dict[str, Any]) -> BaseAgent:
    """Load agent from config"""
    try:
        # Load LLM first
        llm_config = config.get("llm", {})
        llm = load_llm_config(llm_config)
        
        # Create agent with LLM
        agent_type = config.get("type")
        if agent_type not in AGENT_TYPES:
            raise ConfigError(f"Unknown agent type: {agent_type}")
            
        return AGENT_TYPES[agent_type](config, llm)
        
    except Exception as e:
        raise ConfigError(f"Failed to load agent: {str(e)}")

def load_environment_config(config: Dict[str, Any]) -> BaseEnvironment:
    """Load environment from config"""
    try:
        env_type = config.get("type", "default")
        env_config = config.get("config", {})
        env_name = env_config.get("name", f"{env_type}_env")
        
        if env_type not in ENVIRONMENT_TYPES:
            raise ConfigError(f"Unknown environment type: {env_type}")
            
        return ENVIRONMENT_TYPES[env_type](name=env_name, config=env_config)
        
    except Exception as e:
        raise ConfigError(f"Failed to load environment: {str(e)}")

# Register available agent types
AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
    "assistant": AssistantAgent,
    "user": UserAgent,
    # Add other agent types here
}

__all__ = [
    "load_llm_config",
    "load_agent_config",
    "load_environment_config",
    "AGENT_TYPES"
] 