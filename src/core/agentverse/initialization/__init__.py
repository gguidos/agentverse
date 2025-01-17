"""Initialization Module"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import yaml

from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.environment import BaseEnvironment
from src.core.agentverse.llm import get_llm
from src.core.agentverse.exceptions import ConfigError
from src.core.agentverse.config import load_config

logger = logging.getLogger(__name__)

def load_llm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load LLM configuration"""
    try:
        llm_type = config.get("type")
        if not llm_type:
            raise ConfigError("LLM type not specified")
            
        # Get LLM class
        llm = get_llm(llm_type, **config)
        
        return {
            "class": llm.__class__,
            **config
        }
        
    except Exception as e:
        logger.error(f"Failed to load LLM config: {str(e)}")
        raise ConfigError(f"Failed to load LLM config: {str(e)}")

def load_agent_config(config: Dict[str, Any]) -> BaseAgent:
    """Load agent from config"""
    try:
        agent_type = config.get("type", "default")
        agent_name = config.get("name", f"{agent_type}_agent")
        
        # Load agent dependencies
        agent_config = {}
        if "llm" in config:
            llm_config = load_llm_config(config["llm"])
            agent_config["llm"] = llm_config["class"](**llm_config)
        
        # Extract user_id for UserAgent
        if agent_type == "user":
            agent_config["user_id"] = config.get("user_id", agent_name)

        logger.debug(
            f"Loading agent: {agent_type}",
            metadata={"name": agent_name, "config": agent_config}
        )
        
        from src.core.agentverse.agents import AGENT_TYPES
        agent_cls = AGENT_TYPES.get(agent_type)
        if not agent_cls:
            raise ConfigError(f"Unknown agent type: {agent_type}")
            
        return agent_cls(name=agent_name, **agent_config)
        
    except Exception as e:
        logger.error(f"Failed to load agent: {str(e)}")
        raise ConfigError(f"Failed to load agent: {str(e)}")

def load_environment_config(config: Dict[str, Any]) -> BaseEnvironment:
    """Load environment from config"""
    try:
        env_type = config.get("type", "default")
        env_config = config.get("config", {})
        env_name = env_config.get("name") or config.get("name", f"{env_type}_env")

        from src.core.agentverse.environment import ENVIRONMENT_TYPES
        env_cls = ENVIRONMENT_TYPES.get(env_type)
        if not env_cls:
            raise ConfigError(f"Unknown environment type: {env_type}")

        return env_cls(name=env_name, config=env_config)

    except Exception as e:
        logger.error(f"Failed to load environment: {str(e)}")
        raise ConfigError(f"Failed to load environment: {str(e)}") 