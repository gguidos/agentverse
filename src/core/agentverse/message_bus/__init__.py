"""
AgentVerse Message Bus Module

This module provides message bus functionality for agent communication:

1. Message Types:
   - Command: Agent control messages
   - Event: System events
   - Data: Information exchange
   - State: State updates

2. Bus Types:
   - LocalBus: In-process messaging
   - RedisBus: Distributed messaging
   - RabbitMQBus: Advanced message queuing
   - KafkaBus: Stream messaging

3. Features:
   - Pub/Sub patterns
   - Message routing
   - Event handling
   - State management
   - Message persistence

Key Components:
- BaseMessageBus: Core message bus interface
- MessageTypes: Message type definitions
- MessageHandlers: Message processing
- BusConfig: Bus configuration

Example:
    ```python
    from src.core.agentverse.message_bus import LocalMessageBus
    
    # Create message bus
    bus = LocalMessageBus()
    
    # Subscribe to messages
    @bus.subscribe("agent.command")
    async def handle_command(message):
        await process_command(message)
    
    # Publish message
    await bus.publish(
        topic="agent.command",
        message={
            "type": "command",
            "action": "start",
            "agent_id": "agent1"
        }
    )
    ```

Configuration:
```yaml
message_bus:
  type: local
  config:
    persistence: true
    max_queue: 1000
    timeout: 30
  handlers:
    - pattern: "agent.*"
      handler: "agent_handler"
    - pattern: "system.*" 
      handler: "system_handler"
```
"""

from src.core.agentverse.message_bus.base import BaseMessageBus
from src.core.agentverse.message_bus.local import LocalMessageBus
from src.core.agentverse.message_bus.redis import RedisBus
from src.core.agentverse.message_bus.rabbitmq import RabbitMQBus
from src.core.agentverse.message_bus.types import MessageTypes

__all__ = [
    'BaseMessageBus',
    'LocalMessageBus',
    'RedisBus',
    'RabbitMQBus',
    'MessageTypes'
]

# Version
__version__ = "1.0.0" 