"""
Simulation tests
"""

import pytest
from typing import List, Dict, Any
from pytest_asyncio import fixture

from src.core.agentverse.simulation import Simulation, SimulationConfig
from src.core.agentverse.message import Message
from src.core.agentverse.testing.mocks import MockLLM, MockAgent
from src.core.agentverse.exceptions import ConfigError, SimulationError
from src.core.agentverse.environment import EnvironmentStepResult

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
            },
            {
                "type": "user",
                "name": "test_user",
                "user_id": "test_user_1",
                "llm": {
                    "type": "mock",
                    "responses": ["Hi!", "I need help."]
                }
            }
        ],
        "environment": {
            "type": "chat",
            "config": {
                "name": "test_env",
                "max_rounds": 5
            }
        },
        "name": "test_simulation",
        "max_steps": 5
    }

@fixture
async def simulation(mock_config, tmp_path):
    """Create test simulation"""
    # Create test config file
    config_dir = tmp_path / "test_tasks" / "test_simulation"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.yaml"
    
    import yaml
    with open(config_file, "w") as f:
        yaml.dump(mock_config, f)
    
    # Create simulation
    sim = await Simulation.from_task(
        task_name="test_simulation",
        tasks_dir=str(tmp_path / "test_tasks")
    )
    
    yield sim
    
    # Cleanup
    import shutil
    shutil.rmtree(tmp_path)

@pytest.mark.asyncio
async def test_simulation_creation(simulation):
    """Test simulation creation"""
    assert simulation.config.name == "test_simulation"
    assert len(simulation.agents) == 2
    assert simulation.environment is not None

@pytest.mark.asyncio
async def test_simulation_execution(simulation):
    """Test simulation execution"""
    # Run full simulation
    results = await simulation.run()
    
    # Verify results
    assert len(results) > 0
    assert all(r.output for r in results)
    assert len(results) <= simulation.config.max_steps
    
    # Verify metrics collected
    metrics = await simulation.environment.get_metrics()
    assert "steps" in metrics
    assert "history_length" in metrics

@pytest.mark.asyncio
async def test_simulation_step(simulation):
    """Test step-by-step simulation"""
    # Execute single step
    result = await simulation.step()
    
    # Verify result
    assert result.output
    assert not result.done  # First step shouldn't be done
    assert isinstance(result, EnvironmentStepResult)
    
    # Verify history
    assert len(simulation.history) == 1
    
    # Reset simulation
    await simulation.reset()
    assert len(simulation.history) == 0

@pytest.mark.asyncio
async def test_simulation_error_handling():
    """Test simulation error handling"""
    # Try to load non-existent task
    with pytest.raises(SimulationError) as exc:
        await Simulation.from_task(
            task_name="invalid_task",
            tasks_dir="invalid_dir"
        )
    assert "Config not found" in str(exc.value)

@pytest.mark.asyncio
async def test_simulation_metrics(simulation):
    """Test metrics collection"""
    # Run simulation
    results = await simulation.run()
    
    # Get metrics
    metrics = await simulation.environment.get_metrics()
    
    # Verify basic metrics
    assert "steps" in metrics
    assert "history_length" in metrics
    assert metrics["steps"] >= 0
    assert metrics["history_length"] >= 0  # Just verify it's non-negative
    assert len(results) == len(simulation.history)  # Verify simulation history matches results
    
    # Verify agent metrics
    assert "agent_count" in metrics
    assert metrics["agent_count"] == len(simulation.agents) 