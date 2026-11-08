"""Live Fab Telemetry Streaming Service."""

from __future__ import annotations

import random
from datetime import datetime

from fastapi import WebSocket


class TelemetryStreamManager:
    """Manages active WebSocket connections and broadcasts real-time fab events."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


stream_manager = TelemetryStreamManager()


def generate_live_fab_event() -> dict:
    """Generate a single live sensor pulse from a wafer chamber."""
    chambers = ["Chamber_A (CMP)", "Chamber_B (Litho)", "Chamber_C (Etch)"]
    ch = random.choice(chambers)

    # 4% chance of anomaly event
    is_anomaly = random.random() < 0.04
    rf_power = round(random.gauss(13.56, 0.2 if not is_anomaly else 2.5), 2)
    temp = round(random.gauss(65.0, 1.2 if not is_anomaly else 12.0), 1)
    pressure = round(random.gauss(15.2, 0.4 if not is_anomaly else 3.8), 2)
    vibration = round(random.gauss(0.12, 0.02 if not is_anomaly else 0.25), 3)

    now = datetime.utcnow()
    wafer_id = f"W-{now.strftime('%H%M%S')}-{random.randint(100, 999)}"

    return {
        "timestamp": now.isoformat(),
        "wafer_id": wafer_id,
        "chamber": ch,
        "status": "ANOMALY" if is_anomaly else "NORMAL",
        "sensors": {
            "rf_power_kw": rf_power,
            "chamber_temp_c": temp,
            "pressure_mtorr": pressure,
            "vibration_g": vibration,
            "gas_flow_sccm": round(random.gauss(240.0, 5.0), 1),
        },
        "alarm": "High RF Power Deviation" if is_anomaly else None,
    }
