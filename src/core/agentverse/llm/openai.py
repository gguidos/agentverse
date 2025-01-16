"""
OpenAI LLM service implementation
"""

import logging
from typing import Any, Dict, List, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.agentverse.llm.base import BaseLLM
from src.core.agentverse.message import Message  # Updated import path
from src.core.agentverse.exceptions import LLMError

logger = logging.getLogger(__name__)

class OpenAILLM(BaseLLM):
    """OpenAI LLM implementation"""
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize OpenAI LLM
        
        Args:
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            api_key: Optional API key
            **kwargs: Additional model parameters
        """
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        if api_key:
            openai.api_key = api_key
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(self, messages: List[Message]) -> str:
        """Generate text from messages
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If generation fails
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in messages
            ]
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **self.kwargs
            )
            
            # Extract generated text
            generated_text = response.choices[0].message.content
            logger.debug(f"Generated response: {generated_text[:100]}...")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise LLMError(
                message="OpenAI generation failed",
                details={
                    "model": self.model,
                    "error": str(e)
                }
            )
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get text embedding
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
            
        Raises:
            LLMError: If embedding fails
        """
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            raise LLMError(
                message="OpenAI embedding failed",
                details={
                    "error": str(e)
                }
            ) 