from typing import Dict, Any, Optional, List, Union
import openai
import logging

from src.core.agentverse.services.llm.base import (
    BaseLLMService,
    LLMConfig,
    LLMResponse
)
from src.core.agentverse.exceptions import LLMError

logger = logging.getLogger(__name__)

class OpenAIConfig(LLMConfig):
    """OpenAI configuration"""
    api_key: str
    organization: Optional[str] = None
    model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"

class OpenAIService(BaseLLMService):
    """OpenAI LLM service"""
    
    def __init__(self, config: OpenAIConfig):
        """Initialize OpenAI service"""
        super().__init__(config)
        self.config: OpenAIConfig = config
        
        # Configure client
        openai.api_key = config.api_key
        if config.organization:
            openai.organization = config.organization
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI"""
        try:
            # Validate input
            await self._validate_input(prompt)
            
            # Get completion
            response = await openai.ChatCompletion.acreate(
                model=self.config.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                **kwargs
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                usage=response.usage,
                metadata={
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise LLMError(f"Generation failed: {str(e)}")
    
    async def get_embeddings(
        self,
        text: Union[str, List[str]],
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """Get embeddings using OpenAI"""
        try:
            # Validate input
            await self._validate_input(text)
            
            # Get embeddings
            response = await openai.Embedding.acreate(
                model=self.config.embedding_model,
                input=text,
                **kwargs
            )
            
            if isinstance(text, str):
                return response.data[0].embedding
            return [d.embedding for d in response.data]
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            raise LLMError(f"Embedding failed: {str(e)}")
    
    async def evaluate(
        self,
        input: str,
        output: str,
        criteria: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, float]:
        """Evaluate using OpenAI"""
        try:
            # Build evaluation prompt
            prompt = self._build_eval_prompt(input, output, criteria)
            
            # Get evaluation
            response = await self.generate(prompt, **kwargs)
            
            # Parse scores
            scores = self._parse_eval_response(response.text)
            
            return scores
            
        except Exception as e:
            logger.error(f"OpenAI evaluation failed: {str(e)}")
            raise LLMError(f"Evaluation failed: {str(e)}")
    
    def _build_eval_prompt(
        self,
        input: str,
        output: str,
        criteria: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build evaluation prompt"""
        criteria = criteria or {
            "accuracy": "Factual correctness",
            "relevance": "Response relevance",
            "coherence": "Logical flow",
            "helpfulness": "Practical value",
            "safety": "Safety/ethics"
        }
        
        prompt = f"""
        Evaluate the following conversation:
        
        Input: {input}
        Output: {output}
        
        Rate each criterion from 0.0 to 1.0:
        """
        
        for metric, desc in criteria.items():
            prompt += f"\n{metric}: {desc}"
            
        return prompt
    
    def _parse_eval_response(
        self,
        response: str
    ) -> Dict[str, float]:
        """Parse evaluation response"""
        scores = {}
        
        try:
            # Parse scores from response
            for line in response.strip().split("\n"):
                if ":" in line:
                    metric, score = line.split(":")
                    scores[metric.strip()] = float(score.strip())
                    
        except Exception as e:
            logger.error(f"Failed to parse evaluation: {str(e)}")
            
        return scores 