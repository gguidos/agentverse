"""Simulation API endpoints"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import os

from src.core.agentverse.simulation import Simulation

logger = logging.getLogger(__name__)

router = APIRouter()

# Use environment variable or default to /app/tasks
TASKS_DIR = os.getenv("AGENTVERSE_TASKS_DIR", "/app/tasks")

class MessageResponse(BaseModel):
    content: str
    agent: str
    timestamp: datetime

class ChatMessage(BaseModel):
    message: str

@router.get("/simulation/chat", tags=["simulation"])
async def run_chat():
    """Run complete chat simulation"""
    try:
        logger.info("Creating new chat simulation")
        simulation = await Simulation.from_task(
            task_name="simple_chat",
            tasks_dir=TASKS_DIR
        )
        
        logger.info("Running simulation")
        results = await simulation.run()
        
        logger.info(f"Simulation completed with {len(results)} results")
        return {
            "messages": [
                {
                    "content": r.output,
                    "agent": r.metadata.get("agent", "unknown"),
                    "timestamp": r.timestamp
                }
                for r in results
            ],
            "metrics": await simulation.environment.get_metrics()
        }
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "location": "run_chat"
            }
        )

@router.post("/simulation/message", tags=["simulation"], response_model=MessageResponse)
async def send_message(message: ChatMessage):
    """Send message to simulation"""
    try:
        logger.info(f"Processing message: {message.message}")
        simulation = await Simulation.from_task(
            task_name="simple_chat",
            tasks_dir=TASKS_DIR
        )
        
        result = await simulation.step()
        
        return {
            "content": result.output,
            "agent": result.metadata.get("agent", "unknown"),
            "timestamp": result.timestamp
        }
    except Exception as e:
        logger.error(f"Message processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "location": "send_message"
            }
        ) 