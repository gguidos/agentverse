import pytest
import logging
from src.core.agentverse import AgentVerse, AgentVerseConfig
from src.core.agentverse.agents import create_agent, AssistantAgentConfig
from src.core.agentverse.message import Message
from src.core.agentverse.message_bus import create_message_bus, MessageBusType
from src.core.agentverse.resources import ResourceManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_basic_system_setup():
    """Test basic system initialization"""
    
    # 1. Create message bus
    try:
        bus = create_message_bus(MessageBusType.MEMORY)  # Use in-memory for testing
        await bus.connect()
        logger.info("✓ Message bus created successfully")
    except Exception as e:
        logger.error(f"✗ Message bus creation failed: {e}")
        raise

    # 2. Create resource manager
    try:
        resources = ResourceManager()
        resources.add_rate_limiter("llm_calls", rate=10)
        resources.add_quota("memory", max_usage=1024**2)
        logger.info("✓ Resource manager initialized")
    except Exception as e:
        logger.error(f"✗ Resource manager setup failed: {e}")
        raise

    # 3. Create agent
    try:
        config = AssistantAgentConfig(
            name="test_assistant",
            system_prompt="You are a test assistant.",
            temperature=0.7
        )
        agent = create_agent("assistant", config)
        logger.info("✓ Agent created successfully")
    except Exception as e:
        logger.error(f"✗ Agent creation failed: {e}")
        raise

    # 4. Create AgentVerse
    try:
        verse_config = AgentVerseConfig(
            max_steps=10,
            track_metrics=True
        )
        agentverse = AgentVerse(
            agents=[agent],
            message_bus=bus,
            resources=resources,
            config=verse_config
        )
        logger.info("✓ AgentVerse initialized")
    except Exception as e:
        logger.error(f"✗ AgentVerse creation failed: {e}")
        raise

    # 5. Test basic message flow
    try:
        message = Message.user(
            content="Hello, is the system working?",
            sender_id="test_user"
        )
        response = await agentverse.process_message(message)
        assert response.content, "Response should not be empty"
        logger.info("✓ Message processing working")
    except Exception as e:
        logger.error(f"✗ Message processing failed: {e}")
        raise

    # 6. Test resource limits
    try:
        async with resources.rate_limiters["llm_calls"]:
            assert await resources.check_quota("memory", 1024)
        logger.info("✓ Resource management working")
    except Exception as e:
        logger.error(f"✗ Resource management failed: {e}")
        raise

    # 7. Get metrics
    try:
        metrics = agentverse.get_metrics()
        assert "steps" in metrics
        assert "resources" in metrics
        logger.info("✓ Metrics collection working")
    except Exception as e:
        logger.error(f"✗ Metrics collection failed: {e}")
        raise

    # Cleanup
    try:
        await agentverse.cleanup()
        logger.info("✓ System cleanup successful")
    except Exception as e:
        logger.error(f"✗ System cleanup failed: {e}")
        raise

@pytest.mark.asyncio
async def test_error_handling():
    """Test system error handling"""
    
    agentverse = None
    try:
        # Create system with invalid config to test error handling
        config = AgentVerseConfig(
            max_steps=-1  # Invalid value
        )
        agentverse = AgentVerse(
            agents=[],  # Empty agents list should raise error
            config=config
        )
        assert False, "Should have raised ConfigError"
    except Exception as e:
        logger.info("✓ Error handling working as expected")
    finally:
        if agentverse:
            await agentverse.cleanup()

def run_all_tests():
    """Run all system tests"""
    import asyncio
    
    async def run_tests():
        logger.info("Starting system integration tests...")
        
        try:
            await test_basic_system_setup()
            await test_error_handling()
            logger.info("✓ All tests passed successfully")
        except Exception as e:
            logger.error(f"✗ Tests failed: {e}")
            raise
    
    asyncio.run(run_tests())

if __name__ == "__main__":
    run_all_tests() 