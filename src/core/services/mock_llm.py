from typing import Dict, Any

class MockLLM:
    """Mock LLM for testing"""
    
    def __init__(self, model: str = "mock", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        
    async def generate_response(
        self,
        prompt: str,
        message: str = None,  # Add message parameter
        context: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """Generate mock response"""
        # Use message if provided, otherwise use prompt
        input_text = message if message else prompt
        
        # Simple mock responses based on agent type or message content
        if "form" in input_text.lower():
            return "I am a form interviewer. Please answer the following question..."
        elif "research" in input_text.lower():
            return "Let me help you research that topic..."
        elif "evaluate" in input_text.lower():
            return "Based on my evaluation..."
        else:
            return f"Mock response to: {input_text}" 