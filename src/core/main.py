from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    print("Connecting to database...")
    
    yield
    
    # --- Shutdown Logic ---
    print("Closing database connection...")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def hello_world():
    return {"message": "Hello from shtrihs!!!"}