"""Initialization tests"""

import pytest
from pathlib import Path
from typing import Dict, Any

from src.core.agentverse.initialization import (
    load_agent_config,
    load_environment_config,
    load_llm_config
)
from src.core.agentverse.exceptions import ConfigError

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create mock configuration"""
    return {
        "agents": [
            {
                "type": "assistant",
                "name": "test_assistant",
                "llm": {
                    "type": "mock",
                    "responses": ["Hello!", "How can I help?"]
                }
            }
        ],
        "environment": {
            "type": "chat",
            "config": {
                "name": "test_env",
                "max_rounds": 5
            }
        }
    }

async def test_load_llm_config():
    """Test LLM config loading"""
    config = {
        "type": "mock",
        "responses": ["Hello!"]
    }
    
    llm_config = load_llm_config(config)
    assert llm_config["class"] is not None

async def test_load_agent_config(mock_config):
    """Test agent config loading"""
    agent_config = mock_config["agents"][0]
    agent = load_agent_config(agent_config)
    assert agent.name == "test_assistant"

async def test_load_environment_config(mock_config):
    """Test environment config loading"""
    env_config = mock_config["environment"]
    env = load_environment_config(env_config)
    assert env.name == "test_env"

async def test_invalid_llm_type():
    """Test invalid LLM type handling"""
    config = {
        "type": "invalid_llm"
    }
    with pytest.raises(ConfigError):
        load_llm_config(config)

async def test_invalid_agent_type():
    """Test invalid agent type handling"""
    config = {
        "type": "invalid_agent",
        "name": "test"
    }
    with pytest.raises(ConfigError):
        load_agent_config(config)

async def test_invalid_environment_type():
    """Test invalid environment type handling"""
    config = {
        "type": "invalid_env",
        "name": "test"
    }
    with pytest.raises(ConfigError):
        load_environment_config(config) 