from typing import Dict, Any, Optional, List, Union
import anthropic
import logging

from src.core.agentverse.services.llm.base import (
    BaseLLMService,
    LLMConfig,
    LLMResponse
)
from src.core.agentverse.exceptions import LLMError

logger = logging.getLogger(__name__)

class AnthropicConfig(LLMConfig):
    """Anthropic configuration"""
    api_key: str
    model: str = "claude-2"
    max_tokens_to_sample: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = -1
    stop_sequences: List[str] = []

class AnthropicService(BaseLLMService):
    """Anthropic Claude service"""
    
    def __init__(self, config: AnthropicConfig):
        """Initialize Anthropic service"""
        super().__init__(config)
        self.config: AnthropicConfig = config
        
        # Configure client
        self.client = anthropic.Client(api_key=config.api_key)
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Claude"""
        try:
            # Validate input
            await self._validate_input(prompt)
            
            # Get completion
            response = await self.client.completions.create(
                model=self.config.model,
                prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
                max_tokens_to_sample=self.config.max_tokens_to_sample,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                stop_sequences=self.config.stop_sequences,
                **kwargs
            )
            
            return LLMResponse(
                text=response.completion,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={
                    "model": response.model,
                    "stop_reason": response.stop_reason
                }
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise LLMError(f"Generation failed: {str(e)}")
    
    async def get_embeddings(
        self,
        text: Union[str, List[str]],
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """Get embeddings using Claude
        
        Note: Anthropic does not currently provide an embeddings API.
        This is a placeholder that raises an error.
        """
        raise LLMError("Embeddings not supported by Anthropic")
    
    async def evaluate(
        self,
        input: str,
        output: str,
        criteria: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, float]:
        """Evaluate using Claude"""
        try:
            # Build evaluation prompt
            prompt = self._build_eval_prompt(input, output, criteria)
            
            # Get evaluation
            response = await self.generate(prompt, **kwargs)
            
            # Parse scores
            scores = self._parse_eval_response(response.text)
            
            return scores
            
        except Exception as e:
            logger.error(f"Anthropic evaluation failed: {str(e)}")
            raise LLMError(f"Evaluation failed: {str(e)}")
    
    def _build_eval_prompt(
        self,
        input: str,
        output: str,
        criteria: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build evaluation prompt"""
        criteria = criteria or {
            "accuracy": "Factual correctness and precision",
            "relevance": "Response relevance to input",
            "coherence": "Logical flow and clarity",
            "helpfulness": "Practical value and usefulness",
            "safety": "Safety and ethical considerations"
        }
        
        prompt = f"""
        Please evaluate the following conversation objectively:
        
        Input: {input}
        Output: {output}
        
        Rate each criterion from 0.0 (lowest) to 1.0 (highest):
        """
        
        for metric, desc in criteria.items():
            prompt += f"\n{metric}: {desc}"
            
        prompt += "\n\nProvide ratings in the format:\nmetric: score"
            
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
                    try:
                        scores[metric.strip()] = float(score.strip())
                    except ValueError:
                        continue
                    
        except Exception as e:
            logger.error(f"Failed to parse evaluation: {str(e)}")
            
        return scores 