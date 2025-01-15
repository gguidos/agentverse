class AgentTaskQueue:
    """Queue for managing agent tasks"""
    
    def __init__(self, rabbitmq_repository):
        self.queue = rabbitmq_repository
        
    async def enqueue_task(self, agent_id: str, task: dict):
        """Add task to agent's queue"""
        await self.queue.publish_message(
            f"agent.{agent_id}.tasks",
            task
        ) 