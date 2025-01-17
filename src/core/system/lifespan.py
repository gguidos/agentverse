from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
from src.core.consumers.start_rabbit_mq_consumer import start_rabbitmq_consumer
import logging
from threading import Thread
import json
import asyncio

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    """Lifespan event manager to handle startup and shutdown events."""
    container = app.container

    try:
        # Connect to MongoDB
        mongo_client = container.mongo_client()
        await mongo_client.connect()
        logger.info("MongoDB client connected during startup.")

        # Connect to Redis with retry logic
        redis_client = container.redis_client()
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                await redis_client.connect()
                logger.info("Redis client connected during startup.")
                break
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(f"Failed to connect to Redis after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Redis connection attempt {retry_count} failed, retrying...")
                await asyncio.sleep(2)  # Wait 2 seconds before retrying

        await FastAPILimiter.init(redis_client)
        logger.info("Rate limiter initialized with Redis backend.")

        # Start RabbitMQ consumer
        consumer_thread = Thread(target=start_rabbitmq_consumer, args=(container,))
        consumer_thread.daemon = True
        consumer_thread.start()

        yield

    except Exception as e:
        logger.error(f"An error occurred during application startup: {e}")
        raise e

    finally:
        await mongo_client.disconnect()
        if 'redis_client' in locals():
            await redis_client.disconnect()
        logger.info("Clients disconnected during shutdown.")
