from typing import Dict, Any, Optional, List
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.registry import agent_registry
import logging

logger = logging.getLogger(__name__)

@agent_registry.register("form_interviewer")
class FormInterviewerAgent(BaseAgent):
    """Agent for conducting form-based interviews"""
    
    name: str = "form_interviewer"
    description: str = "Agent that conducts form-based interviews"
    version: str = "1.0.0"
    default_capabilities = ["form", "memory"]

    def __init__(
        self,
        name: str,
        llm: Any,
        memory: Optional[BaseMemory] = None,
        parser: Any = None,
        prompt_template: str = "You are a form interviewer assistant.",
        tools: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        session_id: str = None
    ):
        super().__init__(
            name=name,
            llm=llm,
            memory=memory,
            parser=parser,
            prompt_template=prompt_template,
            tools=tools or {},
            metadata=metadata or {}
        )
        self.session_id = session_id

        # Get form config from metadata
        self.form_config = metadata.get("form_config", {})
        self.current_question_index = 0
        
        # We no longer call _load_questions() here because it must be async
        # Instead, we can call it in initialize()
        self.questions: List[Dict[str, Any]] = []

        logger.info(f"Created form interviewer agent: {name}")

    async def initialize(self):
        """Initialize agent resources"""
        # Initialize memory
        logger.debug(f"DEBUG: Entering new initialize() for agent: {self.name}")
        if self.memory:
            await self.memory.initialize()
            # Initialize context with empty answers
            await self._save_context({
                "current_question": None,
                "answers": {},
                "retries": 0
            })

        # Now that we can await, load the questions
        self.questions = await self._load_questions()
        logger.info(f"Initialized {self.name} agent with {len(self.questions)} questions")

    async def _load_questions(self) -> List[Dict[str, Any]]:
        """Load questions either from form_config or from vector store."""
        if not self.form_config:
            return []
        logger.debug(f"Retrieving questions from vector store '{store_name}'")
        # 1) Check if 'questions' is explicitly defined in form_config
        static_questions = self.form_config.get("questions")
        if static_questions:
            logger.debug("Using static questions from form_config")
            return static_questions

        # 2) Otherwise, try to retrieve from the vector store
        store_name = self.form_config.get("form_collection")
        if not store_name:
            logger.debug("No store name provided and no static questions.")
            return []

        logger.debug(f"Retrieving questions from vector store '{store_name}'")

        # Example call to your memory's vectorstore to fetch all chunks
        if not self.memory or not hasattr(self.memory, "vectorstore"):
            logger.warning("No vectorstore found in memory. Returning empty question list.")
            return []

        all_chunks = await self.memory.vectorstore.get_all_chunks(store_name)
        if not all_chunks:
            logger.debug(f"No chunks found for collection '{store_name}'")
            return []

        # 3) Parse text from chunks to find question lines
        question_list = self._parse_questions_from_chunks(all_chunks)
        logger.debug(f"Found {len(question_list)} questions in store '{store_name}'")

        return question_list
    
    def _parse_questions_from_chunks(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """
        Simple parser that looks for lines starting with 'Q:' in each chunk,
        and treats them as a question.
        """
        questions = []
        for chunk in chunks:
            for line in chunk.split("\n"):
                logger.debug(f"Chunk: {chunk}")
                line = line.strip()
                if line.startswith("Q:"):
                    q_text = line.replace("Q:", "").strip()
                    # Example question structure
                    questions.append({"text": q_text, "type": "text"})
        return questions

    async def process_message(self, message: str) -> str:
        """Process incoming message and return response"""
        try:
            # Get interview context from memory
            context = await self.memory.get_context() if self.memory else {}
            
            # If no current question
            if not context.get("current_question"):
                if self.questions:
                    current_q = self.questions[0]
                    await self._save_context({"current_question": current_q})
                    return self._format_question(current_q)
                return "No questions available for this form."

            # Get current question
            current_q = context["current_question"]
            
            # Validate answer if required
            if self.form_config.get("validate_answers", True):
                is_valid = await self._validate_answer(current_q, message)
                if not is_valid:
                    if context.get("retries", 0) >= self.form_config.get("max_retries", 3):
                        return "Maximum retries exceeded. Let's move to the next question."
                    await self._increment_retries(context)
                    return f"Invalid answer. {self._format_question(current_q)}"

            # Store answer
            await self._store_answer(current_q, message)
            
            # Move to next question
            next_q = await self._get_next_question()
            if next_q:
                await self._save_context({"current_question": next_q, "retries": 0})
                return self._format_question(next_q)
            
            # Interview complete
            return "Thank you for completing the form interview!"

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def _format_question(self, question: Dict[str, Any]) -> str:
        """Format question for display"""
        text = question["text"]
        if question.get("type") == "choice" and question.get("options"):
            options = "\n".join(f"- {opt}" for opt in question["options"])
            text = f"{text}\nOptions:\n{options}"
        return text

    async def _validate_answer(self, question: Dict[str, Any], answer: str) -> bool:
        """Validate answer based on question type"""
        q_type = question.get("type", "text")
        
        if q_type == "number":
            try:
                float(answer)
                return True
            except ValueError:
                return False
                
        elif q_type == "choice":
            return answer in question.get("options", [])
            
        # Text type or any other type
        return True

    async def _store_answer(self, question: Dict[str, Any], answer: str):
        """Store answer in memory"""
        if self.memory:
            answers = (await self.memory.get_context()).get("answers", {})
            answers[question["text"]] = answer
            await self._save_context({"answers": answers})

    async def _get_next_question(self) -> Optional[Dict[str, Any]]:
        """Get next question if available"""
        context = await self.memory.get_context() if self.memory else {}
        current_q = context.get("current_question")
        
        if not current_q:
            return self.questions[0] if self.questions else None
            
        # Find current question index
        try:
            current_index = self.questions.index(current_q)
            if current_index + 1 < len(self.questions):
                return self.questions[current_index + 1]
        except ValueError:
            pass
        
        return None

    async def _save_context(self, updates: Dict[str, Any]):
        """Update context in memory"""
        if self.memory:
            context = await self.memory.get_context(self.session_id)
            context.update(updates)
            await self.memory.save_context(context, self.session_id)

    async def _increment_retries(self, context: Dict[str, Any]):
        """Increment retry counter"""
        retries = context.get("retries", 0) + 1
        await self._save_context({"retries": retries}) 

    async def initialize(self):
        """Initialize agent resources"""
        if self.memory:
            await self.memory.initialize()
            # Initialize context with empty answers
            await self._save_context({
                "current_question": None,
                "answers": {},
                "retries": 0
            })
        logger.info(f"Initialized {self.name} agent") 