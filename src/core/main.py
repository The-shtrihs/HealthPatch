import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

import src.core.redis as redis_module
from src.activity.presentation.error_mapper import setup_activity_error_handlers
from src.activity.presentation.routes import router as activity_router
from src.auth.application.event_handlers import register_auth_event_handlers
from src.auth.presentation.error_mapper import setup_auth_error_handlers
from src.auth.presentation.oauth_routes import router as oauth_router
from src.auth.presentation.routes import router as auth_router
from src.core.config import get_settings
from src.core.database import async_session_factory
from src.core.exceptions import setup_exception_handlers
from src.core.tasks.scheduler import scheduler, setup_scheduler
from src.gamification.application.event_handlers import register_gamification_handlers
from src.nutrition.application.event_handlers import register_nutrition_event_handlers
from src.nutrition.presentation.error_mapper import setup_nutrition_error_handlers
from src.nutrition.presentation.routers import router as nutrition_router
from src.shared.infrastructure.daily_claim_store import RedisDailyClaimStore
from src.shared.infrastructure.event_bus import EventBus
from src.shared.infrastructure.event_notification_handlers import register_event_notification_handlers
from src.shared.infrastructure.logging_notify_service import LoggingNotifyService
from src.user.presentation.routes import router as profile_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application...")
    setup_scheduler()
    scheduler.start()
    await redis_module.register_redis(settings)
    event_bus = EventBus()
    await event_bus.start_arq(settings.redis_url)
    register_gamification_handlers(event_bus, async_session_factory, RedisDailyClaimStore())
    register_nutrition_event_handlers(event_bus)
    register_auth_event_handlers(event_bus)
    notify_service = LoggingNotifyService()
    register_event_notification_handlers(event_bus, notify_service)
    app.state.event_bus = event_bus
    yield
    logger.info("Shutting down the application...")
    await redis_module.close_pool()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

setup_exception_handlers(app=app)
setup_auth_error_handlers(app=app)
setup_activity_error_handlers(app=app)
setup_nutrition_error_handlers(app=app)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(oauth_router)
app.include_router(activity_router)
app.include_router(nutrition_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def hello_world():
    return {"message": "Hello from HealthPatch!"}
