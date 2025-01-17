"""Agent Factory Module"""

from typing import Dict, Any, Type
from src.core.agentverse.agents.base import BaseAgent
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.llm import get_llm
from src.core.agentverse.testing.mocks.llm import MockLLM

# Register agent types
AGENT_TYPES = {
    "assistant": AssistantAgent,
    # Add other agent types here
}

def create_agent(agent_type: str, config: Dict[str, Any]) -> BaseAgent:
    """Create agent instance"""
    if agent_type not in AGENT_TYPES:
        raise ValueError(f"Unknown agent type: {agent_type}")
        
    # Get agent class
    agent_class = AGENT_TYPES[agent_type]
    
    # Configure LLM
    llm_config = config.get("llm", {})
    llm_type = llm_config.get("type")
    
    # Use mock LLM for testing
    if llm_type == "mock":
        llm = MockLLM(**llm_config)
    else:
        llm = get_llm(llm_type, **llm_config)
    
    # Create agent
    agent = agent_class(
        name=config["name"],
        llm=llm
    )
    
    return agent 