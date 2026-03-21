from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.exceptions import setup_exception_handlers
from src.core.tasks.scheduler import scheduler, setup_scheduler
from src.routes.auth import router as auth_router
from src.routes.nutrition import router as nutrition_router
from src.routes.oauth import router as oauth_router

app = FastAPI()

setup_exception_handlers(app=app)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    print("Connecting to database...")
    setup_scheduler()
    scheduler.start()

    yield

    # --- Shutdown Logic ---
    print("Closing database connection...")
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

setup_exception_handlers(app=app)
app.include_router(auth_router)
app.include_router(nutrition_router)
app.include_router(oauth_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello from shtrihs!!!"}
