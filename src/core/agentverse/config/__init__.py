"""Config Module"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml

def load_config(task_name: str, tasks_dir: str = None) -> Dict[str, Any]:
    """Load task configuration"""
    if tasks_dir is None:
        tasks_dir = os.getenv("AGENTVERSE_TASKS_DIR", "tasks")
    
    config_path = Path(tasks_dir) / task_name / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
        
    with open(config_path) as f:
        return yaml.safe_load(f) 