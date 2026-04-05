"""
API Routes — All HTTP endpoints for the SafeWay Navigator (Jaipur).
Loads all 8 data layers and passes them to the safety-weighted graph engine.

OPTIMIZED: 
  - Parallel DB loading with asyncio.gather() 
  - In-memory caching of slow-changing data layers (TTL: 60s)
  - Danger pins always loaded fresh (real-time user data)
"""
import secrets
import logging
import time as _time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from graph.pathfinder import calculate_safe_routes
from graph.builder import get_graph, apply_safety_weights
from graph.traffic import get_live_traffic_data
from database.connection import get_pool

import asyncio

logger = logging.getLogger("safeway")
router = APIRouter()

# ── Whitelist of valid PostGIS table names (prevent SQL injection) ─────────────
VALID_TABLES = {
    "streetlights", "crime_records", "businesses", "danger_pins",
    "safe_havens", "cctv_zones", "transit_hubs", "security_points",
}

# ── In-memory cache for safety data layers ────────────────────────────────────
_data_cache = {}
_cache_ttl = 60  # seconds — safety data doesn't change often


async def _load_cached(table: str, extra_cols: str = "") -> list:
    """Load data with in-memory caching (TTL-based)."""
    cache_key = f"{table}:{extra_cols}"
    now = _time.time()

    if cache_key in _data_cache:
        data, ts = _data_cache[cache_key]
        if now - ts < _cache_ttl:
            return data

    data = await _load_spatial_data(table, extra_cols)
    _data_cache[cache_key] = (data, now)
    return data


# ── Request / Response Models ─────────────────────────────────────────────────

class RouteRequest(BaseModel):
    start: List[float] = Field(..., description="[latitude, longitude] of origin")
    end: List[float] = Field(..., description="[latitude, longitude] of destination")
    vehicle_type: str = Field(default="walk", description="walk|bike|drive")

class RouteResponse(BaseModel):
    coordinates: List[List[float]]
    safety_score: int
    distance_m: float
    duration_min: float
    lit_segments: int
    dark_segments: int
    street_names: List[str]
    congestion: List[str] = []
    safe_haven_count: int = 0
    cctv_segments: int = 0
    transit_nearby: int = 0
    road_quality: str = "mixed"
    guardian_token: Optional[str] = None

class DangerPinCreate(BaseModel):
    lat: float
    lng: float
    category: str = Field(..., description="broken_light|suspicious|dog|footpath|loitering|other")
    description: Optional[str] = None

class DangerPinResponse(BaseModel):
    id: int
    lat: float
    lng: float
    category: str
    description: Optional[str]
    created_at: str
    expires_at: str


# ── Health Check ──────────────────────────────────────────────────────────────

@router.get("/api/health")
async def health():
    return {"status": "ok", "city": "Jaipur", "time": datetime.now().isoformat()}


# ── Data Loading Helpers ──────────────────────────────────────────────────────

async def _load_spatial_data(table: str, extra_cols: str = "") -> list:
    """Load lat/lng data from a PostGIS table."""
    if table not in VALID_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    pool = await get_pool()
    extra = f", {extra_cols}" if extra_cols else ""
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT ST_Y(geom::geometry) as lat, ST_X(geom::geometry) as lng{extra}
            FROM {table}
        """)
    return [dict(row) for row in rows]


# ── Safe Route Calculation ────────────────────────────────────────────────────

@router.post("/api/route", response_model=List[RouteResponse])
async def get_safe_route(request: RouteRequest):
    """
    Calculate the top 3 safest pedestrian routes between two points.
    Applies the full 12-factor safety scoring engine.
    
    OPTIMIZED: Loads all 8 data layers in parallel, uses cached data.
    """
    if len(request.start) != 2 or len(request.end) != 2:
        raise HTTPException(status_code=400, detail="start and end must be [lat, lng] arrays")

    start_lat, start_lng = request.start
    end_lat, end_lng = request.end

    t_start = _time.perf_counter()

    try:
        # Load all 8 data layers in PARALLEL using asyncio.gather
        # Cached layers (slow-changing) use _load_cached
        # Danger pins always loaded fresh (real-time user data)
        (
            streetlights,
            crimes,
            businesses,
            danger_pins_data,
            safe_havens,
            cctv_zones,
            transit_hubs,
            security_points,
        ) = await asyncio.gather(
            _load_cached("streetlights"),
            _load_cached("crime_records"),
            _load_cached("businesses", "closing_hour"),
            _load_spatial_data("danger_pins"),  # Always fresh
            _load_cached("safe_havens"),
            _load_cached("cctv_zones"),
            _load_cached("transit_hubs"),
            _load_cached("security_points"),
        )

        t_data = _time.perf_counter()
        logger.info(f"📊 Data loaded in {t_data - t_start:.3f}s (8 layers, {sum(len(x) for x in [streetlights, crimes, businesses, danger_pins_data, safe_havens, cctv_zones, transit_hubs, security_points])} total points)")

        G = get_graph(request.vehicle_type)

        apply_safety_weights(
            G,
            streetlights=streetlights,
            crimes=crimes,
            businesses=businesses,
            danger_pins=danger_pins_data,
            safe_havens=safe_havens,
            cctv_zones=cctv_zones,
            transit_hubs=transit_hubs,
            security_points=security_points,
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=end_lat,
            end_lng=end_lng,
        )

        t_weights = _time.perf_counter()
        logger.info(f"🧮 Safety weights applied in {t_weights - t_data:.3f}s")

        results = calculate_safe_routes(G, start_lat, start_lng, end_lat, end_lng, k_routes=3, vehicle_type=request.vehicle_type)

        t_routes = _time.perf_counter()
        logger.info(f"🗺️ A* pathfinding done in {t_routes - t_weights:.3f}s")
        
        # Fetch live commute times and traffic patches asynchronously for all K routes
        traffic_tasks = [
            get_live_traffic_data(r["coordinates"], request.vehicle_type, r["distance_m"])
            for r in results
        ]
        traffic_results = await asyncio.gather(*traffic_tasks)
        
        for r, traffic_data in zip(results, traffic_results):
            r["duration_min"] = traffic_data["duration_min"]
            r["congestion"] = traffic_data["congestion"]
            r["coordinates"] = traffic_data["coordinates"] # Mapbox snaps to roads, making lines smoother!

        logger.info(f"✅ Total route calculation (with live traffic): {_time.perf_counter() - t_start:.3f}s")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing engine error: {str(e)}")

    guardian_token = secrets.token_urlsafe(12)

    responses = []
    for r in results:
        responses.append(RouteResponse(
            coordinates=r["coordinates"],
            safety_score=r["safety_score"],
            distance_m=r["distance_m"],
            duration_min=r["duration_min"],
            lit_segments=r["lit_segments"],
            dark_segments=r["dark_segments"],
            street_names=r["street_names"],
            congestion=r.get("congestion", []),
            safe_haven_count=r.get("safe_haven_count", 0),
            cctv_segments=r.get("cctv_segments", 0),
            transit_nearby=r.get("transit_nearby", 0),
            road_quality=r.get("road_quality", "mixed"),
            guardian_token=guardian_token,
        ))
        
    return responses


# ── Danger Pins (Community Crowdsourcing) ─────────────────────────────────────

@router.get("/api/danger-pins", response_model=List[DangerPinResponse])
async def get_danger_pins():
    """Return all currently active (non-expired) danger pins."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                id,
                ST_Y(geom::geometry) as lat,
                ST_X(geom::geometry) as lng,
                category,
                description,
                created_at,
                expires_at
            FROM danger_pins
            WHERE expires_at > NOW()
            ORDER BY created_at DESC
            LIMIT 200
        """)

    return [
        DangerPinResponse(
            id=row["id"],
            lat=row["lat"],
            lng=row["lng"],
            category=row["category"],
            description=row["description"],
            created_at=row["created_at"].isoformat(),
            expires_at=row["expires_at"].isoformat(),
        )
        for row in rows
    ]


@router.post("/api/danger-pins", response_model=DangerPinResponse)
async def create_danger_pin(pin: DangerPinCreate):
    """Submit a new community danger warning pin."""
    valid_categories = {"broken_light", "suspicious", "dog", "footpath", "loitering", "other"}
    if pin.category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"category must be one of: {', '.join(valid_categories)}"
        )

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO danger_pins (geom, category, description)
            VALUES (ST_MakePoint($1, $2), $3, $4)
            RETURNING
                id,
                ST_Y(geom::geometry) as lat,
                ST_X(geom::geometry) as lng,
                category, description, created_at, expires_at
        """, pin.lng, pin.lat, pin.category, pin.description)

    pin_res = DangerPinResponse(
        id=row["id"],
        lat=row["lat"],
        lng=row["lng"],
        category=row["category"],
        description=row["description"],
        created_at=row["created_at"].isoformat(),
        expires_at=row["expires_at"].isoformat(),
    )
    
    # Broadcast to Safety Mesh
    from router.socket_manager import manager
    await manager.broadcast_danger_pin(pin_res.dict())
    
    return pin_res


# ── Spatial Stats ────────────────────────────────────────────────────────────

@router.get("/api/stats/streetlights")
async def get_streetlight_count():
    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM streetlights")
    return {"count": count}

@router.get("/api/stats/crimes")
async def get_crime_count():
    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM crime_records")
    return {"count": count}

@router.get("/api/stats/overview")
async def get_data_overview():
    """Return counts of all safety data layers."""
    pool = await get_pool()
    tables = ["streetlights", "crime_records", "businesses", "safe_havens",
              "cctv_zones", "transit_hubs", "security_points", "danger_pins"]
    result = {}
    async with pool.acquire() as conn:
        for t in tables:
            if t not in VALID_TABLES:
                continue
            result[t] = await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
    return result
