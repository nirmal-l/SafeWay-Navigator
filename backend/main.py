import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database.connection import init_db, close_pool
from graph.builder import get_graph
from router.routes import router
from router.socket_manager import manager

load_dotenv()

# ── Production Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("safeway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and graph on startup, clean up on shutdown."""
    logger.info("🚀 Initializing SafeWay Navigator backend...")
    await init_db()
    logger.info("✅ Database initialized (8 PostGIS tables)")
    logger.info("⏳ Graph network will be lazy-loaded on the first user request.")
    yield
    logger.info("🔴 Shutting down...")
    await close_pool()


app = FastAPI(
    title="SafeWay Navigator API",
    description="12-factor safety-weighted routing engine for Jaipur using A* with advanced urban design, temporal, and community metrics",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS — Configurable for production ────────────────────────────────────────
# Set CORS_ORIGINS env var to a comma-separated list of allowed origins
# e.g. "https://safeway.vercel.app,https://www.safeway.app"
# Defaults to "*" for development
_cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if _cors_origins_raw == "*":
    _cors_origins = ["*"]
    _cors_credentials = False
else:
    _cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
    _cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_credentials,
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
        "service": "SafeWay Navigator",
        "city": "Jaipur",
        "version": "2.0 — 12-Factor Safety Engine + WebSockets",
        "status": "running",
        "docs": "/docs",
    }
