from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import asyncio
import logging

from src.core.agentverse.message.base import Message
from src.core.agentverse.monitoring.agent_monitor import AgentMonitor
from src.core.agentverse.exceptions import OrchestrationError

logger = logging.getLogger(__name__)

class WorkflowStep(BaseModel):
    """Model for workflow step"""
    agent_id: str
    task: Dict[str, Any]
    dependencies: List[str] = Field(default_factory=list)
    timeout: Optional[float] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        extra="allow"
    )

class WorkflowConfig(BaseModel):
    """Configuration for workflow execution"""
    max_concurrent_tasks: int = 5
    default_timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    track_metrics: bool = True
    validate_dependencies: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

class AgentOrchestrator:
    """Orchestrates multi-agent workflows"""
    
    name: ClassVar[str] = "agent_orchestrator"
    description: ClassVar[str] = "Multi-agent workflow orchestrator"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        message_bus: Any,
        task_queue: Any,
        monitor: Optional[AgentMonitor] = None,
        config: Optional[WorkflowConfig] = None
    ):
        """Initialize orchestrator
        
        Args:
            message_bus: Message bus instance
            task_queue: Task queue instance
            monitor: Optional agent monitor
            config: Optional workflow configuration
        """
        self.message_bus = message_bus
        self.task_queue = task_queue
        self.monitor = monitor
        self.config = config or WorkflowConfig()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def coordinate_workflow(
        self,
        workflow_id: str,
        steps: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """Coordinate multi-agent workflow
        
        Args:
            workflow_id: Workflow identifier
            steps: Workflow steps to execute
            
        Returns:
            Workflow results
            
        Raises:
            OrchestrationError: If workflow execution fails
        """
        try:
            start_time = datetime.utcnow()
            
            # Validate workflow
            if self.config.validate_dependencies:
                self._validate_workflow(steps)
            
            # Track workflow
            self.active_workflows[workflow_id] = {
                "steps": steps,
                "status": "running",
                "start_time": start_time,
                "results": {}
            }
            
            # Execute steps with dependency handling
            pending_steps = steps.copy()
            running_tasks = set()
            results = {}
            
            while pending_steps or running_tasks:
                # Start ready steps
                ready_steps = [
                    step for step in pending_steps
                    if self._dependencies_met(step, results)
                ]
                
                for step in ready_steps:
                    if len(running_tasks) >= self.config.max_concurrent_tasks:
                        break
                        
                    task = asyncio.create_task(
                        self._execute_step(workflow_id, step)
                    )
                    running_tasks.add(task)
                    pending_steps.remove(step)
                
                # Wait for any task to complete
                if running_tasks:
                    done, running_tasks = await asyncio.wait(
                        running_tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed tasks
                    for task in done:
                        step_id, result = await task
                        results[step_id] = result
            
            # Update workflow status
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.active_workflows[workflow_id].update({
                "status": "completed",
                "duration": duration,
                "results": results
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            self.active_workflows[workflow_id]["status"] = "failed"
            raise OrchestrationError(
                message=f"Workflow execution failed: {str(e)}",
                details={
                    "workflow_id": workflow_id,
                    "steps": len(steps)
                }
            )
        
        finally:
            # Cleanup workflow
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows.pop(workflow_id)
                if self.monitor and self.config.track_metrics:
                    self._update_metrics(workflow)
    
    async def _execute_step(
        self,
        workflow_id: str,
        step: WorkflowStep
    ) -> tuple[str, Any]:
        """Execute workflow step
        
        Args:
            workflow_id: Workflow identifier
            step: Step to execute
            
        Returns:
            Tuple of (step_id, result)
            
        Raises:
            OrchestrationError: If step execution fails
        """
        step_id = f"{workflow_id}_{step.agent_id}"
        retries = 0
        
        while retries <= self.config.max_retries:
            try:
                # Enqueue task
                task_id = await self.task_queue.enqueue_task(
                    agent_id=step.agent_id,
                    task=step.task,
                    timeout=step.timeout or self.config.default_timeout,
                    metadata={
                        "workflow_id": workflow_id,
                        "step_id": step_id,
                        "attempt": retries + 1,
                        **step.metadata
                    }
                )
                
                # Wait for result
                result = await self.task_queue.get_result(task_id)
                
                # Track metrics
                if self.monitor and self.config.track_metrics:
                    self.monitor.track_task(
                        agent_id=step.agent_id,
                        status="success",
                        duration=result.get("duration")
                    )
                
                return step_id, result
                
            except Exception as e:
                retries += 1
                step.retry_count = retries
                
                if retries <= self.config.max_retries:
                    logger.warning(
                        f"Retrying step {step_id} "
                        f"(attempt {retries}/{self.config.max_retries})"
                    )
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    if self.monitor and self.config.track_metrics:
                        self.monitor.track_task(
                            agent_id=step.agent_id,
                            status="failed",
                            error=str(e)
                        )
                    raise OrchestrationError(
                        message=f"Step execution failed: {str(e)}",
                        details={
                            "step_id": step_id,
                            "retries": retries
                        }
                    )
    
    def _validate_workflow(
        self,
        steps: List[WorkflowStep]
    ) -> None:
        """Validate workflow configuration
        
        Args:
            steps: Workflow steps
            
        Raises:
            OrchestrationError: If validation fails
        """
        # Check for circular dependencies
        step_ids = {f"{step.agent_id}" for step in steps}
        
        for step in steps:
            missing = set(step.dependencies) - step_ids
            if missing:
                raise OrchestrationError(
                    message="Invalid step dependencies",
                    details={
                        "step": step.agent_id,
                        "missing": list(missing)
                    }
                )
            
            # Check for circular dependencies
            visited = set()
            def check_circular(step_id: str, path: set) -> None:
                if step_id in path:
                    raise OrchestrationError(
                        message="Circular dependency detected",
                        details={"path": list(path) + [step_id]}
                    )
                if step_id in visited:
                    return
                    
                visited.add(step_id)
                path.add(step_id)
                
                step = next(s for s in steps if s.agent_id == step_id)
                for dep in step.dependencies:
                    check_circular(dep, path.copy())
            
            check_circular(step.agent_id, set())
    
    def _dependencies_met(
        self,
        step: WorkflowStep,
        results: Dict[str, Any]
    ) -> bool:
        """Check if step dependencies are met
        
        Args:
            step: Step to check
            results: Current results
            
        Returns:
            Whether dependencies are met
        """
        return all(
            dep in results
            for dep in step.dependencies
        )
    
    def _update_metrics(
        self,
        workflow: Dict[str, Any]
    ) -> None:
        """Update workflow metrics
        
        Args:
            workflow: Workflow data
        """
        if not self.monitor:
            return
            
        # Update workflow metrics
        duration = workflow.get("duration", 0)
        status = workflow.get("status", "unknown")
        
        self.monitor.track_task(
            agent_id="workflow",
            status=status,
            duration=duration
        )
        
        # Update step metrics
        for step in workflow["steps"]:
            self.monitor.track_task(
                agent_id=step.agent_id,
                status=status,
                duration=duration / len(workflow["steps"])
            )
    
    def get_workflow_status(
        self,
        workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get workflow status
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Optional workflow status
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
            
        return {
            "status": workflow["status"],
            "start_time": workflow["start_time"],
            "duration": (
                (datetime.utcnow() - workflow["start_time"]).total_seconds()
                if workflow["status"] == "running"
                else workflow.get("duration")
            ),
            "steps_total": len(workflow["steps"]),
            "steps_completed": len(workflow["results"])
        } 