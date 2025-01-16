from typing import Dict, Set, Any, Optional, ClassVar, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.visibility.base import (
    BaseVisibility,
    VisibilityConfig,
    VisibilityMetrics
)
from src.core.agentverse.environment.registry import visibility_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class GroupConfig(BaseModel):
    """Configuration for a group"""
    name: str
    members: Set[str] = Field(default_factory=set)
    visible_to: Set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GroupVisibilityConfig(VisibilityConfig):
    """Configuration for group visibility"""
    groups: Dict[str, GroupConfig] = Field(default_factory=dict)
    allow_cross_group: bool = True
    allow_self_visibility: bool = True
    inherit_visibility: bool = True
    track_group_changes: bool = True
    validate_groups: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class GroupMetrics(VisibilityMetrics):
    """Additional metrics for group visibility"""
    group_changes: int = 0
    cross_group_visibility: int = 0
    group_sizes: Dict[str, int] = Field(default_factory=dict)
    group_interactions: Dict[str, Dict[str, int]] = Field(default_factory=dict)

@visibility_registry.register("group")
class GroupVisibility(BaseVisibility):
    """Visibility handler based on agent groups"""
    
    name: ClassVar[str] = "group_visibility"
    description: ClassVar[str] = "Visibility handler based on agent groups"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[GroupVisibilityConfig] = None
    ):
        super().__init__(config=config or GroupVisibilityConfig())
        self.group_metrics = GroupMetrics()
        self._validate_group_config()
    
    def _validate_group_config(self) -> None:
        """Validate group configuration
        
        Raises:
            ActionError: If configuration is invalid
        """
        try:
            if not self.config.groups:
                return
            
            # Check for duplicate members
            all_members = set()
            for group in self.config.groups.values():
                overlap = all_members & group.members
                if overlap:
                    raise ValueError(
                        f"Agents {overlap} belong to multiple groups"
                    )
                all_members.update(group.members)
            
            # Check visible_to references
            all_groups = set(self.config.groups.keys())
            for group in self.config.groups.values():
                invalid = group.visible_to - all_groups
                if invalid:
                    raise ValueError(
                        f"Group {group.name} references invalid groups: {invalid}"
                    )
            
        except Exception as e:
            raise ActionError(
                message=f"Invalid group configuration: {str(e)}",
                action=self.name,
                details={"groups": list(self.config.groups.keys())}
            )
    
    async def _update_visibility(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update visibility based on groups
        
        Args:
            environment: Environment to update visibility for
            
        Raises:
            ActionError: If update fails
        """
        try:
            # Track old visibility for change detection
            old_visibility = (
                self.state.visibility_map.copy()
                if self.config.track_group_changes
                else {}
            )
            
            # Update visibility for each agent
            for agent in environment.agents:
                visible = await self._get_visible_agents(
                    agent.name,
                    environment
                )
                
                # Remove self if configured
                if not self.config.allow_self_visibility:
                    visible.discard(agent.name)
                
                self.state.visibility_map[agent.name] = visible
                
                # Update agent's receiver set if supported
                if hasattr(agent, 'set_receiver'):
                    await agent.set_receiver(visible)
            
            # Track changes if configured
            if self.config.track_group_changes:
                self._track_group_changes(old_visibility)
            
            # Update group metrics
            self._update_group_metrics(environment)
            
        except Exception as e:
            logger.error(f"Group visibility update failed: {str(e)}")
            raise ActionError(
                message=str(e),
                action=self.name,
                details={
                    "groups": list(self.config.groups.keys()),
                    "agents": len(environment.agents)
                }
            )
    
    async def _get_visible_agents(
        self,
        agent_name: str,
        environment: BaseEnvironment
    ) -> Set[str]:
        """Get visible agents for an agent
        
        Args:
            agent_name: Agent to get visibility for
            environment: Environment instance
            
        Returns:
            Set of visible agent names
        """
        visible = set()
        
        # Find agent's groups
        agent_groups = [
            group for group in self.config.groups.values()
            if agent_name in group.members
        ]
        
        for group in agent_groups:
            # Add group members
            visible.update(group.members)
            
            # Add visible groups if cross-group visibility allowed
            if self.config.allow_cross_group:
                for visible_group in self.config.groups.values():
                    if (
                        visible_group.name in group.visible_to or
                        (
                            self.config.inherit_visibility and
                            any(
                                vg in group.visible_to
                                for vg in visible_group.visible_to
                            )
                        )
                    ):
                        visible.update(visible_group.members)
                        self.group_metrics.cross_group_visibility += 1
        
        return visible
    
    def _track_group_changes(
        self,
        old_visibility: Dict[str, Set[str]]
    ) -> None:
        """Track group visibility changes
        
        Args:
            old_visibility: Previous visibility state
        """
        for agent, new_visible in self.state.visibility_map.items():
            old_visible = old_visibility.get(agent, set())
            
            # Track changes
            if new_visible != old_visible:
                self.group_metrics.group_changes += 1
                
                # Update group interaction stats
                agent_group = self._get_agent_group(agent)
                if agent_group:
                    interactions = self.group_metrics.group_interactions.setdefault(
                        agent_group,
                        {}
                    )
                    
                    for visible in new_visible - old_visible:
                        visible_group = self._get_agent_group(visible)
                        if visible_group:
                            interactions[visible_group] = (
                                interactions.get(visible_group, 0) + 1
                            )
    
    def _get_agent_group(self, agent_name: str) -> Optional[str]:
        """Get group name for an agent
        
        Args:
            agent_name: Agent to get group for
            
        Returns:
            Optional group name
        """
        for group_name, group in self.config.groups.items():
            if agent_name in group.members:
                return group_name
        return None
    
    def _update_group_metrics(
        self,
        environment: BaseEnvironment
    ) -> None:
        """Update group metrics
        
        Args:
            environment: Environment instance
        """
        # Update group sizes
        self.group_metrics.group_sizes = {
            name: len(group.members)
            for name, group in self.config.groups.items()
        }
        
        # Update agent stats
        for agent in environment.agents:
            group = self._get_agent_group(agent.name)
            if group:
                stats = self.group_metrics.agent_stats.setdefault(
                    agent.name,
                    {"group": group, "visible_count": 0}
                )
                stats["visible_count"] = len(
                    self.state.visibility_map.get(agent.name, set())
                )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics including group metrics
        
        Returns:
            Combined metrics
        """
        metrics = super().get_metrics()
        group_metrics = self.group_metrics.model_dump()
        
        # Add group visibility ratio
        if self.group_metrics.group_changes > 0:
            group_metrics["cross_group_ratio"] = (
                self.group_metrics.cross_group_visibility /
                self.group_metrics.group_changes
            )
        
        metrics.update(group_metrics)
        return metrics
    
    def reset(self) -> None:
        """Reset visibility state"""
        super().reset()
        self.group_metrics = GroupMetrics()
        logger.info(f"Reset {self.name} visibility handler") 