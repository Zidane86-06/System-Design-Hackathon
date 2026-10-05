from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import init_db
from app.redis_client import redis_gate
from app.event_bus import event_bus
from app.services.reservation_worker import reservation_worker
from app.api import products, inventory, orders, payments, reservations, simulation, metrics

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print(f"Starting {settings.PROJECT_NAME}...")
    await init_db()
    await redis_gate.connect()
    await event_bus.connect()
    await reservation_worker.start()
    yield
    # Shutdown actions
    print("Shutting down SALESTORM background workers...")
    await reservation_worker.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-Concurrency Flash-Sale Platform Prototype (10,000 requests / 100 inventory guarantee)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(reservations.router)
app.include_router(simulation.router)
app.include_router(metrics.router)

@app.get("/")
async def root():
    return {
        "platform": "SALESTORM",
        "status": "ONLINE",
        "guarantee": "10,000 Concurrent Users -> 100 Available Units -> Max Sales <= 100, 0 Overselling",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
