import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database.connection import init_db
from graph.builder import get_graph
from router.routes import router
from router.socket_manager import manager

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and graph on startup."""
    print("🚀 Initializing Fear-Free Night Navigator backend...")
    await init_db()
    print("✅ Database initialized (8 PostGIS tables)")
    print("⏳ Graph network will be lazy-loaded on the first user request.")
    yield
    print("🔴 Shutting down...")


app = FastAPI(
    title="Fear-Free Night Navigator API",
    description="12-factor safety-weighted routing engine for Jaipur using A* with advanced urban design, temporal, and community metrics",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin (Vercel, localhost, etc.)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.websocket("/ws/safety")
async def websocket_safety_endpoint(websocket: WebSocket):
    """Global channel for active users. Receives their GPS, broadcasts Danger Pins."""
    await manager.connect_safety(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                # If a user is sending their live coordinates tied to a guardian token
                if payload.get("type") == "LIVE_LOCATION" and payload.get("token"):
                    # Broadcast to anyone watching that token
                    await manager.broadcast_guardian_location(payload["token"], payload)
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect_safety(websocket)

@app.websocket("/ws/guardian/{token}")
async def websocket_guardian_endpoint(websocket: WebSocket, token: str):
    """Specific channel for a Guardian Observer watching a token."""
    await manager.connect_guardian(websocket, token)
    try:
        while True:
            await websocket.receive_text() # Just keep alive, observer doesn't send much
    except WebSocketDisconnect:
        manager.disconnect_guardian(websocket, token)

@app.get("/")
async def root():
    return {
        "service": "Fear-Free Night Navigator",
        "city": "Jaipur",
        "version": "2.0 — 12-Factor Safety Engine + WebSockets",
        "status": "running",
        "docs": "/docs",
    }
