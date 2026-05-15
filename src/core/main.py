import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

import src.core.redis as redis_module
from src.analytics_context.audit.application.handlers import configure as configure_audit_handlers
from src.analytics_context.audit.application.handlers import register_audit_handlers
from src.analytics_context.audit.presentation.routes import router as analytics_audit_router
from src.analytics_context.projections.activity_history.handlers import (
    configure as configure_activity_history_projection,
)
from src.analytics_context.projections.activity_history.handlers import (
    register_projection_handlers as register_activity_history_handlers,
)
from src.core.config import get_settings
from src.core.database import async_session_factory
from src.core.exceptions import setup_exception_handlers
from src.core.tasks.scheduler import scheduler, setup_scheduler
from src.core_context.activity.application.event_handlers import register_activity_event_handlers
from src.core_context.activity.application.integration_publishers import register_activity_integration_publishers
from src.core_context.activity.infrastructure.audit_service import LoggingActivityAuditService
from src.core_context.activity.presentation.error_mapper import setup_activity_error_handlers
from src.core_context.activity.presentation.routes import router as activity_router
from src.core_context.auth.application.event_handlers import register_auth_event_handlers
from src.core_context.auth.infrastructure.audit_service import LoggingAuthAuditService
from src.core_context.auth.presentation.error_mapper import setup_auth_error_handlers
from src.core_context.auth.presentation.oauth_routes import router as oauth_router
from src.core_context.auth.presentation.routes import router as auth_router
from src.core_context.gamification.application.event_handlers import register_gamification_handlers
from src.core_context.nutrition.application.event_handlers import register_nutrition_event_handlers
from src.core_context.nutrition.application.integration_publishers import register_nutrition_integration_publishers
from src.core_context.nutrition.infrastructure.audit_service import LoggingNutritionAuditService
from src.core_context.nutrition.infrastructure.diary_directory import SqlMealEntryQueries
from src.core_context.nutrition.presentation.error_mapper import setup_nutrition_error_handlers
from src.core_context.nutrition.presentation.routers import router as nutrition_router
from src.core_context.user.presentation.routes import router as profile_router
from src.shared.infrastructure.daily_claim_store import RedisDailyClaimStore
from src.shared.infrastructure.event_bus import EventBus

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
    register_activity_integration_publishers(event_bus)
    register_nutrition_integration_publishers(event_bus)

    register_gamification_handlers(
        event_bus,
        async_session_factory,
        SqlMealEntryQueries(async_session_factory),
        RedisDailyClaimStore(),
    )
    register_nutrition_event_handlers(event_bus, LoggingNutritionAuditService())
    register_auth_event_handlers(event_bus, LoggingAuthAuditService())
    register_activity_event_handlers(event_bus, LoggingActivityAuditService())

    configure_audit_handlers(async_session_factory)
    register_audit_handlers(event_bus)
    configure_activity_history_projection(async_session_factory)
    register_activity_history_handlers(event_bus)
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
app.include_router(analytics_audit_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def hello_world():
    return {"message": "Hello from HealthPatch!"}
