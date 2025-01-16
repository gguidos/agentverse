"""Distributed Tracing Module"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import contextvars
import uuid
import time

class TraceContext(BaseModel):
    """Trace context information"""
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Span(BaseModel):
    """Trace span information"""
    id: str
    trace_id: str
    parent_id: Optional[str] = None
    name: str
    start_time: float
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TracingManager:
    """Distributed tracing management"""
    
    _context = contextvars.ContextVar("trace_context")
    
    @classmethod
    def start_span(
        cls,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start new trace span"""
        # Get or create trace context
        try:
            context = cls._context.get()
            parent_id = context.span_id
            trace_id = context.trace_id
        except LookupError:
            parent_id = None
            trace_id = str(uuid.uuid4())
        
        # Create span
        span = Span(
            id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        # Update context
        cls._context.set(TraceContext(
            trace_id=span.trace_id,
            span_id=span.id,
            parent_id=span.parent_id
        ))
        
        return span
    
    @classmethod
    def end_span(cls, span: Span) -> None:
        """End trace span"""
        span.end_time = time.time() 