"""
Database connection and initialization using asyncpg.
Supports PostGIS spatial tables for the Jaipur safety engine.
"""
import os
import logging
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("safeway")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ffnn_user:ffnn_password@localhost:5433/ffnn_db")
_pool = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        # Retry logic for cold-start DB connections (Render free tier wakes up slowly)
        for attempt in range(3):
            try:
                _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
                break
            except Exception as e:
                if attempt < 2:
                    logger.warning(f"DB connection attempt {attempt + 1} failed, retrying in 2s: {e}")
                    await asyncio.sleep(2)
                else:
                    raise
    return _pool


async def close_pool():
    """Gracefully close the connection pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")


async def init_db():
    """Create all PostGIS tables if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # ── Streetlights ─────────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS streetlights (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                source TEXT DEFAULT 'seeded'
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_streetlights_geom ON streetlights USING GIST(geom);")

        # ── Crime Records ────────────────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS crime_records (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                category TEXT NOT NULL,
                severity INTEGER DEFAULT 1,
                recorded_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_crimes_geom ON crime_records USING GIST(geom);")

        # ── Danger Pins (Crowdsourced) ───────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS danger_pins (
                id SERIAL PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours')
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_danger_geom ON danger_pins USING GIST(geom);")

        # ── Businesses (with closing hour) ───────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT,
                category TEXT,
                open_late BOOLEAN DEFAULT FALSE,
                closing_hour INTEGER DEFAULT 0
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_business_geom ON businesses USING GIST(geom);")

        # ── Safe Havens (Police, Hospitals, Fire Stations) ───────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS safe_havens (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT,
                category TEXT,
                is_24x7 BOOLEAN DEFAULT TRUE
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_safe_haven_geom ON safe_havens USING GIST(geom);")

        # ── CCTV / Surveillance Zones ────────────────────────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cctv_zones (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                location_name TEXT,
                camera_count INTEGER DEFAULT 1
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_cctv_geom ON cctv_zones USING GIST(geom);")

        # ── Transit Hubs (Bus stops, Auto stands, Metro) ─────────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transit_hubs (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT,
                hub_type TEXT,
                is_24x7 BOOLEAN DEFAULT FALSE
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_transit_geom ON transit_hubs USING GIST(geom);")

        # ── Security Points (ATMs, Hotels, Gated Societies) ──────────────
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_points (
                id TEXT PRIMARY KEY,
                geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT,
                point_type TEXT
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_security_geom ON security_points USING GIST(geom);")

    logger.info("✅ PostGIS tables initialized (8 tables for Jaipur safety engine)")
