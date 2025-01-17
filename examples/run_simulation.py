"""Run simulation server"""

import asyncio
from aiohttp import web
from src.core.agentverse.simulation import Simulation

async def run_chat(request):
    """Handle chat simulation request"""
    try:
        simulation = await Simulation.from_task(
            task_name="simple_chat",
            tasks_dir="examples"
        )
        results = await simulation.run()
        return web.json_response({
            "messages": [
                {
                    "content": r.output,
                    "agent": r.metadata["agent"],
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ],
            "metrics": await simulation.environment.get_metrics()
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def send_message(request):
    """Handle new message"""
    try:
        data = await request.json()
        message = data.get("message", "")
        simulation = request.app["simulation"]
        result = await simulation.step()
        return web.json_response({
            "response": result.output,
            "agent": result.metadata["agent"],
            "timestamp": result.timestamp.isoformat()
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def init():
    app = web.Application()
    app.router.add_get('/chat', run_chat)
    app.router.add_post('/chat/message', send_message)
    app["simulation"] = await Simulation.from_task("simple_chat", "examples")
    return app

if __name__ == '__main__':
    app = asyncio.get_event_loop().run_until_complete(init())
    web.run_app(app, port=8080) 