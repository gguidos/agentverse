from typing import List, Dict, Any, Optional, ClassVar
import logging
from string import Template
from datetime import datetime

from src.core.agentverse.environment.describers.base import (
    BaseDescriber,
    EnvironmentContext,
    DescriberConfig
)
from src.core.agentverse.environment.registry import describer_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import EnvironmentError

logger = logging.getLogger(__name__)

class BasicDescriberConfig(DescriberConfig):
    """Configuration for basic describer"""
    include_history: bool = False  # Minimal by default
    include_metrics: bool = False
    include_agent_states: bool = True
    template: str = """
Turn: ${turn}${max_turns}
Agents: ${agent_count}
Active Agent: ${active_agent}
Status: ${status}
${agent_info}
${metrics_summary}
"""
    show_agent_details: bool = True
    show_metrics_summary: bool = True
    max_agent_details: int = 3

@describer_registry.register("basic")
class BasicDescriber(BaseDescriber):
    """Basic environment describer with minimal context"""
    
    name: ClassVar[str] = "basic_describer"
    description: ClassVar[str] = "Basic environment describer with configurable templates"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(self, config: Optional[BasicDescriberConfig] = None):
        super().__init__(config=config or BasicDescriberConfig())
        self.template = Template(self.config.template)
        logger.info(f"Initialized basic describer with template")
    
    async def _generate_descriptions(
        self,
        environment: BaseEnvironment,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> List[EnvironmentContext]:
        """Generate minimal descriptions
        
        Args:
            environment: Environment to describe
            agent_id: Optional agent ID to filter for
            **kwargs: Additional arguments
            
        Returns:
            List of environment contexts
        """
        try:
            descriptions = []
            
            # Get agents to describe for
            target_agents = (
                [agent_id] if agent_id is not None
                else list(environment.state.agents)
            )
            
            for current_agent_id in target_agents:
                # Build template variables
                template_vars = self._build_template_vars(
                    environment,
                    current_agent_id
                )
                
                # Create context
                context = EnvironmentContext(
                    description=self.template.safe_substitute(template_vars),
                    turn=environment.state.current_turn,
                    agent_count=len(environment.state.agents),
                    active_agents={environment.state.active_agent}
                    if environment.state.active_agent else set(),
                    metadata={
                        "agent_id": current_agent_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "template_vars": template_vars
                    }
                )
                
                descriptions.append(context)
            
            return descriptions
            
        except Exception as e:
            logger.error(f"Failed to generate basic description: {str(e)}")
            raise EnvironmentError(f"Description generation failed: {str(e)}")
    
    def _build_template_vars(
        self,
        environment: BaseEnvironment,
        agent_id: str
    ) -> Dict[str, str]:
        """Build template variables
        
        Args:
            environment: Environment instance
            agent_id: Current agent ID
            
        Returns:
            Dict of template variables
        """
        # Basic variables
        vars = {
            "turn": str(environment.state.current_turn),
            "max_turns": (
                f"/{environment.state.max_turns}"
                if environment.state.max_turns
                else ""
            ),
            "agent_count": str(len(environment.state.agents)),
            "active_agent": (
                environment.state.active_agent
                if environment.state.active_agent
                else "None"
            ),
            "status": environment.state.status
        }
        
        # Add agent details if configured
        if self.config.show_agent_details:
            vars["agent_info"] = self._format_agent_details(
                environment,
                agent_id
            )
        else:
            vars["agent_info"] = ""
        
        # Add metrics summary if configured
        if self.config.show_metrics_summary:
            vars["metrics_summary"] = self._format_metrics_summary(
                environment
            )
        else:
            vars["metrics_summary"] = ""
        
        return vars
    
    def _format_agent_details(
        self,
        environment: BaseEnvironment,
        current_agent_id: str
    ) -> str:
        """Format agent details section
        
        Args:
            environment: Environment instance
            current_agent_id: Current agent ID
            
        Returns:
            Formatted agent details
        """
        if not environment.state.agents:
            return "No agents present"
        
        # Get agent states
        states = environment.state.agent_states
        
        # Format details for each agent
        details = []
        for i, agent_id in enumerate(environment.state.agents):
            if i >= self.config.max_agent_details:
                details.append("...")
                break
                
            state = states.get(agent_id, {})
            status = state.get("status", "unknown")
            
            if agent_id == current_agent_id:
                details.append(f"* {agent_id} (you): {status}")
            else:
                details.append(f"* {agent_id}: {status}")
        
        return "\nAgents:\n" + "\n".join(details)
    
    def _format_metrics_summary(
        self,
        environment: BaseEnvironment
    ) -> str:
        """Format metrics summary section
        
        Args:
            environment: Environment instance
            
        Returns:
            Formatted metrics summary
        """
        metrics = environment.state.metrics
        if not metrics:
            return ""
        
        # Select key metrics
        summary = [
            f"\nMetrics:",
            f"* Messages: {metrics.get('total_messages', 0)}",
            f"* Steps: {metrics.get('total_steps', 0)}",
            f"* Errors: {metrics.get('error_count', 0)}"
        ]
        
        # Add performance metrics if available
        if "avg_step_duration" in metrics:
            summary.append(
                f"* Avg Duration: {metrics['avg_step_duration']:.2f}s"
            )
        
        return "\n".join(summary)
    
    def reset(self) -> None:
        """Reset describer state"""
        super().reset()
        self.template = Template(self.config.template) 