from .traits import EvaluatorTraits

class AgentConfig(BaseModel):
    name: str
    type: str
    capabilities: List[str] = []
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    evaluator_traits: Optional[EvaluatorTraits] = None 