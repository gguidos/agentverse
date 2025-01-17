"""
Example of running a simulation
"""

import asyncio
from src.core.agentverse.simulation import Simulation
from src.core.agentverse.logging import logger

async def main():
    # Create simulation from task config
    simulation = await Simulation.from_task(
        task_name="chat_simulation",
        tasks_dir="examples"
    )
    
    # Method 1: Run entire simulation
    results = await simulation.run()
    
    # Print results
    for i, result in enumerate(results):
        print(f"Step {i+1}:")
        print(f"Output: {result.output}")
        print(f"Metrics: {result.metrics}")
        print("---")
    
    # Method 2: Step through simulation manually
    simulation.reset()
    
    while not simulation.environment.is_done():
        # Execute single step
        result = await simulation.step()
        
        # Process result
        print(f"Step output: {result.output}")
        
        # Access metrics
        if result.metrics:
            print(f"Metrics: {result.metrics}")

if __name__ == "__main__":
    asyncio.run(main()) 