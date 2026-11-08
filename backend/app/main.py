"""WaferGuard Production MLOps Backend Application."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import API_PREFIX, CORS_ORIGINS
from backend.app.db.database import init_db
from backend.app.routers import datasets, models, monitoring, predict, train
from backend.app.services.telemetry_stream import (
    generate_live_fab_event,
    stream_manager,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("waferguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing WaferGuard database schemas...")
    init_db()

    # Launch background simulated telemetry streamer task
    stream_task = asyncio.create_task(_background_telemetry_broadcaster())
    logger.info("WaferGuard MLOps platform ready.")
    yield
    stream_task.cancel()
    logger.info("WaferGuard platform shutting down.")


async def _background_telemetry_broadcaster():
    """Periodically emits simulated sensor telemetry events to active WebSockets."""
    while True:
        try:
            if stream_manager.active_connections:
                event = generate_live_fab_event()
                await stream_manager.broadcast(event)
            await asyncio.sleep(1.8)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in telemetry broadcast loop: {e}")
            await asyncio.sleep(2.0)


app = FastAPI(
    title="WaferGuard MLOps API",
    description="Industrial Predictive Maintenance & Sensor Anomaly Detection for Semiconductor Manufacturing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(datasets.router, prefix=API_PREFIX)
app.include_router(train.router, prefix=API_PREFIX)
app.include_router(models.router, prefix=API_PREFIX)
app.include_router(predict.router, prefix=API_PREFIX)
app.include_router(monitoring.router, prefix=API_PREFIX)


@app.get("/health", tags=["System"])
def health_check():
    """Health status and service availability."""
    return {
        "status": "healthy",
        "service": "WaferGuard MLOps Platform",
        "version": "1.0.0",
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """Real-time semiconductor chamber sensor telemetry WebSocket."""
    await stream_manager.connect(websocket)
    try:
        while True:
            # Keep connection open, handle client messages if sent
            await websocket.receive_text()
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception:
        stream_manager.disconnect(websocket)


# Mount frontend build if built
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
