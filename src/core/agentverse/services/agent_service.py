from ..agents.models.traits import EvaluatorTraits, EvaluationStyle

class AgentService:
    async def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent"""
        try:
            # Handle evaluator configuration if present
            if config.get("type") == "evaluator":
                evaluator_config = config.get("evaluator_traits", {})
                traits = EvaluatorTraits(
                    style=evaluator_config.get("style", EvaluationStyle.NEUTRAL),
                    confidence_threshold=evaluator_config.get("confidence_threshold", 0.7),
                    bias_factors=evaluator_config.get("bias_factors", {}),
                    focus_areas=evaluator_config.get("focus_areas", [])
                )
                config["evaluator_traits"] = traits.dict()
            
            # Create agent with configuration
            agent = await self.agent_factory.create_agent(config)
            return {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type,
                "capabilities": agent.capabilities,
                "evaluator_traits": agent.evaluator_traits.dict() if agent.evaluator_traits else None
            }
            
        except Exception as e:
            logger.error(f"Agent creation failed: {str(e)}")
            raise AgentCreationError(f"Failed to create agent: {str(e)}") 