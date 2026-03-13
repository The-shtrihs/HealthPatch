from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    print("Connecting to database...")

    yield

    # --- Shutdown Logic ---
    print("Closing database connection...")


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)


@app.get("/")
async def hello_world():
    return {"message": "Hello from shtrihs!!!"}
