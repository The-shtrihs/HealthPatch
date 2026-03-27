import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

import src.core.redis as redis_module
from src.core.config import get_settings
from src.core.exceptions import setup_exception_handlers
from src.core.tasks.scheduler import scheduler, setup_scheduler
from src.routes.activity import router as activity_router
from src.routes.auth import router as auth_router
from src.routes.nutrition import router as nutrition_router
from src.routes.oauth import router as oauth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    logger.info("Starting up the application...")
    logger.info("Setting up the scheduler...")
    setup_scheduler()
    scheduler.start()

    redis_module._pool = redis_module.create_pool(
        url=settings.redis_url,
        max_connections=settings.redis_max_connections,
    )

    redis = redis_module.get_redis()

    try:
        pong = await redis.ping()
        logger.info(f"Connected to Redis: {settings.redis_url}, ping response: {pong}")

    except Exception as e:
        logger.error(f"Failed to connect to Redis at {settings.redis_url}: {e}")
        raise

    yield

    # --- Shutdown Logic ---
    logger.info("Shutting down the application...")
    logger.info("Closing Redis connection pool...")
    await redis_module.close_pool()
    logger.info("Redis connection pool closed.")
    logger.info("Shutting down the scheduler...")
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

setup_exception_handlers(app=app)
app.include_router(activity_router)
app.include_router(auth_router)
app.include_router(nutrition_router)
app.include_router(oauth_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello from shtrihs!!!"}
