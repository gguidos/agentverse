from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.actions import AgentAction, AgentStep, ActionSequence
from src.core.agentverse.message.base import Message
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.registry import agent_registry
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class FormField(BaseModel):
    """Form field configuration"""
    name: str
    question: str
    required: bool = True
    validation: Optional[str] = None
    default: Optional[str] = None
    
    model_config = ConfigDict(
        extra="allow"
    )

class FormSchema(BaseModel):
    """Form schema configuration"""
    fields: Dict[str, FormField]
    title: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    model_config = ConfigDict(
        extra="allow"
    )

class FormState(BaseModel):
    """State for form interview"""
    current_form: Optional[str] = None
    current_field: Optional[str] = None
    answers: Dict[str, str] = Field(default_factory=dict)
    form_schema: Optional[FormSchema] = None
    start_time: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class FormInterviewerConfig(BaseModel):
    """Configuration for form interviewer"""
    validate_answers: bool = True
    allow_skipping: bool = False
    track_history: bool = True
    max_retries: int = 3
    temperature: float = 0.7
    
    model_config = ConfigDict(
        extra="allow"
    )

@agent_registry.register("form_interviewer")
class FormInterviewerAgent(BaseAgent):
    """Agent for conducting form-based interviews"""
    
    name: ClassVar[str] = "form_interviewer"
    description: ClassVar[str] = "Form interview agent"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        memory: BaseMemory,
        config: Optional[FormInterviewerConfig] = None
    ):
        """Initialize form interviewer agent"""
        super().__init__(
            llm_service=llm_service,
            memory=memory,
            config=config or FormInterviewerConfig()
        )
        self.state = FormState()
        self.action_sequence = ActionSequence()
        logger.info(f"Initialized {self.name} v{self.version}")
    
    async def start_interview(
        self,
        form_name: str
    ) -> Message:
        """Start new interview session
        
        Args:
            form_name: Form identifier
            
        Returns:
            First question message
            
        Raises:
            AgentError: If start fails
        """
        try:
            # Create start action
            action = AgentAction(
                tool="start_interview",
                input={"form_name": form_name}
            )
            step = AgentStep(action=action)
            
            try:
                # Get form context
                form_chunks = await self.memory.search(
                    query=f"form structure for {form_name}",
                    k=5
                )
                
                if not form_chunks:
                    raise AgentError(
                        message=f"Form not found: {form_name}",
                        details={"available_forms": await self.memory.list_forms()}
                    )
                
                # Parse form schema
                form_text = "\n".join(form_chunks)
                self.state.form_schema = await self._parse_form_schema(form_text)
                self.state.current_form = form_name
                self.state.start_time = datetime.utcnow()
                
                # Get first question
                first_field = next(iter(self.state.form_schema.fields))
                self.state.current_field = first_field
                
                # Update action/step
                action.complete(
                    output={
                        "form": form_name,
                        "first_field": first_field
                    },
                    duration=step.duration
                )
                step.complete({
                    "form": form_name,
                    "first_field": first_field
                })
                
            except Exception as e:
                action.fail(str(e))
                step.fail(str(e))
                logger.error(f"Interview start failed: {str(e)}")
                raise
            
            # Track step
            self.action_sequence.add_step(step)
            
            # Create first question message
            return Message(
                content=self.state.form_schema.fields[first_field].question,
                sender=self.name,
                receiver={"user"},
                metadata={
                    "form": form_name,
                    "field": first_field,
                    "required": self.state.form_schema.fields[first_field].required
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to start interview: {str(e)}")
            raise AgentError(
                message=f"Failed to start interview: {str(e)}",
                details={"form": form_name}
            )
    
    async def process_answer(
        self,
        answer: str
    ) -> Message:
        """Process answer and get next question
        
        Args:
            answer: User's answer
            
        Returns:
            Next question message
            
        Raises:
            AgentError: If processing fails
        """
        try:
            if not self.state.current_field:
                raise AgentError(
                    message="No active interview session",
                    details={"last_form": self.state.current_form}
                )
            
            # Create answer action
            action = AgentAction(
                tool="process_answer",
                input={
                    "field": self.state.current_field,
                    "answer": answer
                }
            )
            step = AgentStep(action=action)
            
            try:
                # Validate answer if configured
                if self.config.validate_answers:
                    await self._validate_answer(
                        self.state.current_field,
                        answer
                    )
                
                # Store answer
                self.state.answers[self.state.current_field] = answer
                self.state.last_interaction = datetime.utcnow()
                
                # Get next field
                next_field = await self._get_next_field()
                
                # Update action/step
                action.complete(
                    output={
                        "field": self.state.current_field,
                        "next_field": next_field
                    },
                    duration=step.duration
                )
                step.complete({
                    "field": self.state.current_field,
                    "next_field": next_field
                })
                
            except Exception as e:
                action.fail(str(e))
                step.fail(str(e))
                logger.error(f"Answer processing failed: {str(e)}")
                raise
            
            # Track step
            self.action_sequence.add_step(step)
            
            # Check if interview is complete
            if not next_field:
                return await self.generate_final_text()
            
            # Update current field
            self.state.current_field = next_field
            
            # Return next question
            return Message(
                content=self.state.form_schema.fields[next_field].question,
                sender=self.name,
                receiver={"user"},
                metadata={
                    "form": self.state.current_form,
                    "field": next_field,
                    "required": self.state.form_schema.fields[next_field].required,
                    "progress": len(self.state.answers) / len(self.state.form_schema.fields)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process answer: {str(e)}")
            raise AgentError(
                message=f"Failed to process answer: {str(e)}",
                details={
                    "field": self.state.current_field,
                    "answer_length": len(answer)
                }
            )
    
    async def generate_final_text(self) -> Message:
        """Generate final text from answers
        
        Returns:
            Final text message
            
        Raises:
            AgentError: If generation fails
        """
        try:
            # Create generation action
            action = AgentAction(
                tool="generate_final",
                input={
                    "form": self.state.current_form,
                    "answers": self.state.answers
                }
            )
            step = AgentStep(action=action)
            
            try:
                # Build prompt
                prompt = (
                    f"Form: {self.state.form_schema.title}\n\n"
                    f"Answers:\n{self._format_answers()}\n\n"
                    "Generate a complete text incorporating all answers. "
                    "Make it flow naturally and be well-structured."
                )
                
                # Get response
                response = await self.llm.chat_completion(
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=self.config.temperature
                )
                
                final_text = response.choices[0].message.content
                
                # Update action/step
                action.complete(
                    output={"text": final_text},
                    duration=step.duration
                )
                step.complete({"text": final_text})
                
            except Exception as e:
                action.fail(str(e))
                step.fail(str(e))
                logger.error(f"Final text generation failed: {str(e)}")
                raise
            
            # Track step
            self.action_sequence.add_step(step)
            
            # Return final message
            return Message(
                content=final_text,
                sender=self.name,
                receiver={"user"},
                metadata={
                    "form": self.state.current_form,
                    "is_final": True,
                    "fields_completed": len(self.state.answers),
                    "duration": (
                        datetime.utcnow() - self.state.start_time
                    ).total_seconds() if self.state.start_time else None
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate final text: {str(e)}")
            raise AgentError(
                message=f"Failed to generate final text: {str(e)}",
                details={
                    "form": self.state.current_form,
                    "answers": len(self.state.answers)
                }
            )
    
    async def _parse_form_schema(
        self,
        form_text: str
    ) -> FormSchema:
        """Parse form schema from text
        
        Args:
            form_text: Form schema text
            
        Returns:
            Parsed form schema
            
        Raises:
            AgentError: If parsing fails
        """
        try:
            # Get schema with LLM
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Extract form schema from text. "
                        "Return JSON with fields, title, and description."
                    )
                },
                {
                    "role": "user",
                    "content": form_text
                }
            ]
            
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=0.1
            )
            
            # Parse response
            import json
            schema_dict = json.loads(response.choices[0].message.content)
            
            return FormSchema(**schema_dict)
            
        except Exception as e:
            logger.error(f"Form schema parsing failed: {str(e)}")
            raise AgentError(
                message=f"Failed to parse form schema: {str(e)}",
                details={"text_length": len(form_text)}
            )
    
    async def _validate_answer(
        self,
        field: str,
        answer: str
    ) -> None:
        """Validate answer for field
        
        Args:
            field: Field name
            answer: Answer to validate
            
        Raises:
            AgentError: If validation fails
        """
        field_config = self.state.form_schema.fields[field]
        
        # Check required
        if field_config.required and not answer.strip():
            raise AgentError(
                message=f"Field '{field}' is required",
                details={"field": field}
            )
        
        # Check validation rule if any
        if field_config.validation:
            # Add validation logic here
            pass
    
    async def _get_next_field(self) -> Optional[str]:
        """Get next field to ask
        
        Returns:
            Next field name or None if complete
        """
        fields = list(self.state.form_schema.fields.keys())
        current_idx = fields.index(self.state.current_field)
        
        if current_idx < len(fields) - 1:
            return fields[current_idx + 1]
        return None
    
    def _format_answers(self) -> str:
        """Format answers for prompt
        
        Returns:
            Formatted answers text
        """
        if not self.state.answers:
            return "No answers yet."
        
        return "\n".join([
            f"Q: {self.state.form_schema.fields[field].question}\n"
            f"A: {answer}"
            for field, answer in self.state.answers.items()
        ])
    
    async def reset(self) -> None:
        """Reset agent state"""
        await super().reset()
        self.state = FormState()
        self.action_sequence = ActionSequence() 