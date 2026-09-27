import asyncio
import json
import math
import random
import time
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI(title="Dynamic Visualization Backend")

# Enable CORS for local web interface access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manage WebSocket client connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()


# -------------------------------------------------------------------
# Synthetic Generators (Time Series, Candlesticks, 3D Mesh)
# -------------------------------------------------------------------

def generate_telemetry_tick(t: float) -> dict:
    """Generates time-series wave values with controllable noise."""
    base_val = math.sin(t * 0.1) * 30 + math.cos(t * 0.05) * 15
    noise = random.uniform(-5, 5)
    
    # Inject synthetic anomalies (~2% probability)
    anomaly = random.choice([25, -25]) if random.random() < 0.02 else 0
    value = base_val + noise + anomaly

    return {
        "type": "telemetry",
        "timestamp": int(time.time() * 1000),
        "value": round(value, 2),
        "is_anomaly": abs(anomaly) > 0
    }

def generate_candlestick_tick(current_price: float) -> tuple[dict, float]:
    """Simulates realistic asset price movements using Brownian motion."""
    change = random.gauss(0, 1.5)
    open_p = current_price
    close_p = open_p + change
    high_p = max(open_p, close_p) + abs(random.gauss(0, 0.8))
    low_p = min(open_p, close_p) - abs(random.gauss(0, 0.8))
    volume = int(random.uniform(100, 5000))

    data = {
        "type": "candlestick",
        "timestamp": int(time.time() * 1000),
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "close": round(close_p, 2),
        "volume": volume
    }
    return data, close_p


# -------------------------------------------------------------------
# Background Streaming Task
# -------------------------------------------------------------------

async def stream_engine():
    """Background loop broadcasting dynamic telemetry and financial data."""
    t = 0.0
    price = 150.00
    
    while True:
        if manager.active_connections:
            # 1. Telemetry Tick
            telemetry_data = generate_telemetry_tick(t)
            await manager.broadcast(telemetry_data)
            
            # 2. Candlestick Tick (Every ~3 seconds)
            if int(t) % 3 == 0:
                candle_data, price = generate_candlestick_tick(price)
                await manager.broadcast(candle_data)

            t += 0.2
        await asyncio.sleep(0.2)  # Stream frequency: 5 Hz


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(stream_engine())


# -------------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------------

@app.get("/api/initial-batch")
async def get_initial_batch(points: int = 100):
    """Generates initial historical data array for dashboard hydration."""
    now = time.time()
    batch = []
    val = 100.0
    
    for i in range(points):
        ts = int((now - (points - i) * 2) * 1000)
        val += random.uniform(-2, 2)
        batch.append({
            "timestamp": ts,
            "value": round(val, 2)
        })
        
    return {"status": "success", "data": batch}


@app.get("/api/surface-mesh")
async def get_3d_surface(rows: int = 20, cols: int = 20):
    """Calculates dynamic 3D surface array coordinates via NumPy."""
    x = np.linspace(-3, 3, cols)
    y = np.linspace(-3, 3, rows)
    X, Y = np.meshgrid(x, y)
    
    # Calculating 3D ripples z = sin(x^2 + y^2)
    Z = np.sin(np.sqrt(X**2 + Y**2)) * 2.0
    
    return {
        "rows": rows,
        "cols": cols,
        "x": x.tolist(),
        "y": y.tolist(),
        "z": Z.tolist()
    }


# -------------------------------------------------------------------
# WebSocket Endpoint
# -------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive commands or runtime configuration parameters from client
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            if payload.get("action") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": int(time.time() * 1000)})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
