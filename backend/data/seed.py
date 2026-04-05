"""
Jaipur Data Seeder — Seeds PostgreSQL/PostGIS with comprehensive Jaipur safety data.

Run this ONCE after docker compose up:
    cd backend && python data/seed.py

Data is geographically accurate (real Jaipur coordinates).
Safety classifications are synthesized for demonstration but placed at real locations.

Tables seeded:
  1. streetlights       — Street lighting clusters
  2. crime_records      — Crime hot zones
  3. businesses         — Late-night shops with closing hours
  4. safe_havens        — Police stations, hospitals, fire stations
  5. cctv_zones         — CCTV / surveillance camera locations
  6. transit_hubs       — Bus terminals, auto stands, metro stations
  7. security_points    — ATMs, hotels, gated societies
"""
import asyncio
import os
import random
import uuid

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ffnn_user:ffnn_password@localhost:5433/ffnn_db")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. STREETLIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
STREETLIGHT_CLUSTERS = [
    # (lat, lng, area_name, density)
    # MI Road — Commercial hub, well-lit
    (26.9155, 75.8040, "MI Road", 55),
    (26.9168, 75.8082, "Panch Batti", 50),
    # Raja Park — Bustling shopping and food district
    (26.8967, 75.8288, "Raja Park Main Market", 45),
    # JLN Marg — Wide, well-lit smart city boulevard
    (26.8631, 75.8153, "JLN Marg South", 45),
    (26.8837, 75.8130, "JLN Marg / Ram Niwas Bagh", 40),
    (26.8750, 75.8140, "JLN Marg Central", 40),
    # C-Scheme — Upscale area
    (26.9079, 75.7977, "C-Scheme Central", 50),
    (26.9042, 75.8011, "Statue Circle", 40),
    # Malviya Nagar — Commercial / Residential
    (26.8502, 75.8167, "Malviya Nagar Sector 3", 35),
    (26.8530, 75.8180, "Gaurav Tower (GT)", 45),
    # Vaishali Nagar
    (26.9126, 75.7428, "Vaishali Nagar Amrapali Circle", 38),
    # Tonk Road
    (26.8800, 75.8050, "Tonk Road", 35),
    # Ajmer Road
    (26.9100, 75.7600, "Ajmer Road", 30),
    # Mansarovar
    (26.8700, 75.7600, "Mansarovar", 30),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CRIME HOT ZONES
# ═══════════════════════════════════════════════════════════════════════════════
CRIME_CLUSTERS = [
    # (lat, lng, area_name, n_crimes, severity_range)
    # Old Pink City boundaries — Dense, crowded tourists, pickpockets
    (26.9239, 75.8267, "Hawa Mahal Area", 40, (1, 3)),
    (26.9268, 75.8229, "Badi Chaupar", 45, (1, 3)),
    (26.9234, 75.8161, "Chandpole Bazar", 35, (2, 4)),
    # Railway Station / Sindhi Camp — Budget hotels and transit chaos
    (26.9196, 75.7878, "Jaipur Junction", 45, (2, 4)),
    (26.9235, 75.7946, "Sindhi Camp Bus Stand", 50, (2, 4)),
    # Sikar Road — Isolated industrial stretches
    (26.9649, 75.7725, "Sikar Road Industrial Area", 30, (2, 5)),
    # Jagatpura — Newly developing, dark stretches
    (26.8242, 75.8506, "Jagatpura Outskirts", 35, (2, 4)),
    # Sanganer — Semi-urban
    (26.8100, 75.7900, "Sanganer Area", 25, (1, 3)),
    # Galta Gate area — Dense old-city
    (26.9200, 75.8500, "Galta Gate", 30, (2, 3)),
    # Safe areas (low crime) — for contrast
    (26.9079, 75.7977, "C-Scheme", 5, (1, 1)),
    (26.8631, 75.8153, "JLN Marg", 3, (1, 1)),
    (26.8530, 75.8180, "Malviya Nagar", 5, (1, 1)),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BUSINESSES (with closing hours)
# ═══════════════════════════════════════════════════════════════════════════════
BUSINESSES = [
    # (lat, lng, name, category, open_late, closing_hour)
    # 0 = 24/7, 23 = closes 11PM, 22 = closes 10PM, etc.

    # 24/7 Pharmacies
    (26.9155, 75.8040, "Apollo Pharmacy MI Road", "pharmacy", True, 0),
    (26.8967, 75.8288, "24hr Pharmacy Raja Park", "pharmacy", True, 0),
    (26.9126, 75.7428, "MedPlus Vaishali Nagar", "pharmacy", True, 0),
    (26.8530, 75.8180, "MedPlus Malviya Nagar", "pharmacy", True, 0),

    # Hospitals (always open)
    (26.8943, 75.8080, "SMS Hospital", "hospital", True, 0),
    (26.8407, 75.8002, "Fortis Hospital", "hospital", True, 0),
    (26.8623, 75.7431, "Shalby Hospital", "hospital", True, 0),
    (26.9050, 75.8300, "Narayana Multispecialty", "hospital", True, 0),

    # Petrol Pumps (24/7, well-lit)
    (26.9042, 75.8011, "HPCL Statue Circle", "fuel", True, 0),
    (26.9196, 75.7878, "IOCL Railway Station", "fuel", True, 0),
    (26.8800, 75.8050, "BPCL Tonk Road", "fuel", True, 0),

    # Late-night restaurants (close around 12AM-1AM)
    (26.8960, 75.8285, "Sethi Tikka Raja Park", "restaurant", True, 0),
    (26.9190, 75.7940, "Rawat Kachori", "restaurant", True, 23),
    (26.9155, 75.8060, "Niros MI Road", "restaurant", True, 23),
    (26.8530, 75.8200, "Sizzler N Grill GT", "restaurant", True, 23),

    # Markets (close early)
    (26.9239, 75.8267, "Hawa Mahal Bazar", "market", False, 21),
    (26.9268, 75.8229, "Badi Chaupar Market", "market", False, 21),
    (26.9234, 75.8161, "Chandpole Bazar", "market", False, 21),
    (26.8967, 75.8310, "Raja Park Market", "market", False, 22),

    # Metro Stations (close around midnight)
    (26.9200, 75.7885, "Railway Station Metro", "transit", True, 0),
    (26.9230, 75.7950, "Sindhi Camp Metro", "transit", True, 0),
    (26.9160, 75.8100, "Chandpole Metro", "transit", True, 0),
    (26.9060, 75.7970, "Civil Lines Metro", "transit", True, 0),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SAFE HAVENS (Police, Hospitals, Fire Stations)
# ═══════════════════════════════════════════════════════════════════════════════
SAFE_HAVENS = [
    # (lat, lng, name, category, is_24x7)
    # Police Stations
    (26.9170, 75.8070, "MI Road Police Station", "police", True),
    (26.9080, 75.7980, "Ashok Nagar Police Chowki", "police", True),
    (26.8960, 75.8290, "Raja Park Police Station", "police", True),
    (26.9240, 75.8260, "Manak Chowk Police Stn", "police", True),
    (26.9200, 75.7880, "Railway Station Police Post", "police", True),
    (26.8700, 75.8150, "JLN Marg Police Chowki", "police", True),
    (26.8500, 75.8170, "Malviya Nagar Police Stn", "police", True),
    (26.9120, 75.7420, "Vaishali Nagar Police Stn", "police", True),
    (26.8800, 75.8060, "Tonk Road Police Chowki", "police", True),

    # Hospitals (24/7)
    (26.8943, 75.8080, "SMS Hospital", "hospital", True),
    (26.8407, 75.8002, "Fortis Escort Hospital", "hospital", True),
    (26.8623, 75.7431, "Shalby Hospital", "hospital", True),
    (26.9050, 75.8300, "Narayana Multispecialty", "hospital", True),
    (26.8750, 75.8200, "Santokba Durlabhji Hospital", "hospital", True),

    # Fire Stations
    (26.9190, 75.7870, "Jaipur Main Fire Station", "fire_station", True),
    (26.8650, 75.8100, "Civil Lines Fire Station", "fire_station", True),
    (26.9100, 75.7600, "Ajmer Road Fire Post", "fire_station", True),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CCTV / SURVEILLANCE ZONES
# ═══════════════════════════════════════════════════════════════════════════════
CCTV_ZONES = [
    # (lat, lng, location_name, camera_count)
    # JLN Marg — Smart City corridor (extensive coverage)
    (26.8631, 75.8153, "JLN Marg / SMS Hospital Junction", 6),
    (26.8700, 75.8140, "JLN Marg / Rambagh Circle", 5),
    (26.8750, 75.8140, "JLN Marg / Tonk Road Cross", 5),
    (26.8837, 75.8130, "JLN Marg / Ram Niwas Bagh", 4),

    # MI Road
    (26.9155, 75.8040, "MI Road / Panch Batti", 6),
    (26.9168, 75.8082, "MI Road / Ajmeri Gate", 4),
    (26.9140, 75.8000, "MI Road / Raj Mandir Cinema", 4),

    # Tonk Road
    (26.8800, 75.8050, "Tonk Road / Durgapura", 4),
    (26.8900, 75.8070, "Tonk Road / SFS Mansarovar", 3),

    # Ajmer Road
    (26.9100, 75.7600, "Ajmer Road / Panchyawala", 3),

    # Traffic intersections
    (26.9042, 75.8011, "Statue Circle", 5),
    (26.9079, 75.7977, "C-Scheme / Prithviraj Road", 4),
    (26.8967, 75.8288, "Raja Park Crossing", 3),
    (26.9239, 75.8267, "Hawa Mahal Junction", 4),
    (26.9268, 75.8229, "Badi Chaupar", 3),

    # Railway / Metro zone
    (26.9200, 75.7885, "Jaipur Junction CCTV", 8),
    (26.9235, 75.7946, "Sindhi Camp CCTV", 5),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. TRANSIT HUBS (Bus, Auto, Metro)
# ═══════════════════════════════════════════════════════════════════════════════
TRANSIT_HUBS = [
    # (lat, lng, name, hub_type, is_24x7)
    # Bus Terminals
    (26.9235, 75.7946, "Sindhi Camp ISBT", "bus_terminal", True),
    (26.8450, 75.8050, "Durgapura Bus Stand", "bus_stand", False),

    # Railway
    (26.9196, 75.7878, "Jaipur Junction Railway Stn", "railway", True),
    (26.8350, 75.7870, "Gandhinagar Railway Stn", "railway", True),

    # Metro Stations
    (26.9200, 75.7885, "Jaipur Metro - Railway Stn", "metro", False),
    (26.9230, 75.7950, "Jaipur Metro - Sindhi Camp", "metro", False),
    (26.9160, 75.8100, "Jaipur Metro - Chandpole", "metro", False),
    (26.9060, 75.7970, "Jaipur Metro - Civil Lines", "metro", False),
    (26.8960, 75.7940, "Jaipur Metro - Ram Nagar", "metro", False),

    # Major Auto-Rickshaw Stands
    (26.9196, 75.7900, "Auto Stand - Railway Station", "auto_stand", True),
    (26.9042, 75.8011, "Auto Stand - Statue Circle", "auto_stand", True),
    (26.8967, 75.8270, "Auto Stand - Raja Park", "auto_stand", True),
    (26.9155, 75.8040, "Auto Stand - MI Road", "auto_stand", True),
    (26.8530, 75.8180, "Auto Stand - Malviya Nagar", "auto_stand", True),
    (26.8700, 75.7600, "Auto Stand - Mansarovar", "auto_stand", True),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SECURITY POINTS (ATMs, Hotels, Gated Societies)
# ═══════════════════════════════════════════════════════════════════════════════
SECURITY_POINTS = [
    # (lat, lng, name, point_type)
    # ATMs (typically have guards in India)
    (26.9155, 75.8050, "SBI ATM MI Road", "atm"),
    (26.9042, 75.8020, "HDFC ATM Statue Circle", "atm"),
    (26.8967, 75.8295, "ICICI ATM Raja Park", "atm"),
    (26.8530, 75.8190, "Axis ATM Malviya Nagar", "atm"),
    (26.9126, 75.7435, "SBI ATM Vaishali Nagar", "atm"),
    (26.8800, 75.8060, "HDFC ATM Tonk Road", "atm"),
    (26.8700, 75.8155, "PNB ATM JLN Marg", "atm"),
    (26.9190, 75.7890, "BOB ATM Railway Station", "atm"),
    (26.9079, 75.7985, "IDBI ATM C-Scheme", "atm"),
    (26.8630, 75.8160, "Kotak ATM JLN Marg S", "atm"),

    # Major Hotels (24/7 security, well-lit entrances)
    (26.9050, 75.8010, "ITC Rajputana", "hotel"),
    (26.9030, 75.7990, "Marriott Jaipur", "hotel"),
    (26.8700, 75.8130, "Hilton Jaipur", "hotel"),
    (26.9170, 75.8100, "Hotel Clark Amer", "hotel"),
    (26.9120, 75.7950, "Holiday Inn", "hotel"),
    (26.8530, 75.8150, "Radisson Jaipur City Center", "hotel"),

    # Gated / Guard-Staffed Societies
    (26.8967, 75.8230, "Ganesh Nagar Gate", "gated_society"),
    (26.9079, 75.7950, "C-Scheme Sector 3 Gate", "gated_society"),
    (26.8700, 75.7580, "Mansarovar Sector 7 Gate", "gated_society"),
    (26.9126, 75.7410, "Vaishali E-Block Gate", "gated_society"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# SEEDING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_streetlights(conn):
    print("💡 Seeding streetlights...")
    count = 0
    random.seed(42)
    for lat, lng, area, density in STREETLIGHT_CLUSTERS:
        for i in range(density):
            uid = str(uuid.uuid4())
            dlat = random.uniform(-0.0018, 0.0018)
            dlng = random.uniform(-0.0018, 0.0018)
            await conn.execute("""
                INSERT INTO streetlights (id, geom, source)
                VALUES ($1, ST_MakePoint($2, $3), $4)
                ON CONFLICT (id) DO NOTHING
            """, uid, lng + dlng, lat + dlat, area)
            count += 1
    print(f"   ✅ Seeded {count} streetlights")


async def seed_crimes(conn):
    print("🚨 Seeding crime data...")
    count = 0
    categories = ["theft", "harassment", "vandalism", "assault", "suspicious_activity", "chain_snatching", "eve_teasing"]
    random.seed(123)
    for lat, lng, area, n_crimes, sev_range in CRIME_CLUSTERS:
        for i in range(n_crimes):
            uid = str(uuid.uuid4())
            dlat = random.uniform(-0.003, 0.003)
            dlng = random.uniform(-0.003, 0.003)
            category = random.choice(categories)
            severity = random.randint(*sev_range)
            await conn.execute("""
                INSERT INTO crime_records (id, geom, category, severity)
                VALUES ($1, ST_MakePoint($2, $3), $4, $5)
                ON CONFLICT (id) DO NOTHING
            """, uid, lng + dlng, lat + dlat, category, severity)
            count += 1
    print(f"   ✅ Seeded {count} crime records")


async def seed_businesses(conn):
    print("🏪 Seeding businesses (with closing hours)...")
    for lat, lng, name, category, open_late, closing_hour in BUSINESSES:
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, name))
        await conn.execute("""
            INSERT INTO businesses (id, geom, name, category, open_late, closing_hour)
            VALUES ($1, ST_MakePoint($2, $3), $4, $5, $6, $7)
            ON CONFLICT (id) DO NOTHING
        """, uid, lng, lat, name, category, open_late, closing_hour)
    print(f"   ✅ Seeded {len(BUSINESSES)} businesses")


async def seed_safe_havens(conn):
    print("🏛️ Seeding safe havens (police, hospitals, fire stations)...")
    for lat, lng, name, category, is_24x7 in SAFE_HAVENS:
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, name))
        await conn.execute("""
            INSERT INTO safe_havens (id, geom, name, category, is_24x7)
            VALUES ($1, ST_MakePoint($2, $3), $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
        """, uid, lng, lat, name, category, is_24x7)
    print(f"   ✅ Seeded {len(SAFE_HAVENS)} safe havens")


async def seed_cctv_zones(conn):
    print("📹 Seeding CCTV / surveillance zones...")
    count = 0
    random.seed(456)
    for lat, lng, location, cam_count in CCTV_ZONES:
        for c in range(cam_count):
            uid = str(uuid.uuid4())
            dlat = random.uniform(-0.0005, 0.0005)
            dlng = random.uniform(-0.0005, 0.0005)
            await conn.execute("""
                INSERT INTO cctv_zones (id, geom, location_name, camera_count)
                VALUES ($1, ST_MakePoint($2, $3), $4, 1)
                ON CONFLICT (id) DO NOTHING
            """, uid, lng + dlng, lat + dlat, location)
            count += 1
    print(f"   ✅ Seeded {count} CCTV camera points")


async def seed_transit_hubs(conn):
    print("🚌 Seeding transit hubs...")
    for lat, lng, name, hub_type, is_24x7 in TRANSIT_HUBS:
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, name))
        await conn.execute("""
            INSERT INTO transit_hubs (id, geom, name, hub_type, is_24x7)
            VALUES ($1, ST_MakePoint($2, $3), $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
        """, uid, lng, lat, name, hub_type, is_24x7)
    print(f"   ✅ Seeded {len(TRANSIT_HUBS)} transit hubs")


async def seed_security_points(conn):
    print("🔐 Seeding security points (ATMs, hotels, gated societies)...")
    for lat, lng, name, point_type in SECURITY_POINTS:
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, name))
        await conn.execute("""
            INSERT INTO security_points (id, geom, name, point_type)
            VALUES ($1, ST_MakePoint($2, $3), $4, $5)
            ON CONFLICT (id) DO NOTHING
        """, uid, lng, lat, name, point_type)
    print(f"   ✅ Seeded {len(SECURITY_POINTS)} security points")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("🌱 SafeWay Navigator — Jaipur Data Seeder (v2: 12-Factor)")
    print("=" * 60)
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # Create all tables
        for table in ["streetlights", "crime_records", "businesses", "danger_pins",
                       "safe_havens", "cctv_zones", "transit_hubs", "security_points"]:
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

        # Recreate tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS streetlights (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL, source TEXT DEFAULT 'seeded'
            ); CREATE INDEX IF NOT EXISTS idx_sl_geom ON streetlights USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS crime_records (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                category TEXT NOT NULL, severity INTEGER DEFAULT 1, recorded_at TIMESTAMP DEFAULT NOW()
            ); CREATE INDEX IF NOT EXISTS idx_cr_geom ON crime_records USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT, category TEXT, open_late BOOLEAN DEFAULT FALSE, closing_hour INTEGER DEFAULT 0
            ); CREATE INDEX IF NOT EXISTS idx_biz_geom ON businesses USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS danger_pins (
                id SERIAL PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                category TEXT NOT NULL, description TEXT,
                created_at TIMESTAMP DEFAULT NOW(), expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours')
            ); CREATE INDEX IF NOT EXISTS idx_dp_geom ON danger_pins USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS safe_havens (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT, category TEXT, is_24x7 BOOLEAN DEFAULT TRUE
            ); CREATE INDEX IF NOT EXISTS idx_sh_geom ON safe_havens USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cctv_zones (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                location_name TEXT, camera_count INTEGER DEFAULT 1
            ); CREATE INDEX IF NOT EXISTS idx_cctv_geom ON cctv_zones USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transit_hubs (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT, hub_type TEXT, is_24x7 BOOLEAN DEFAULT FALSE
            ); CREATE INDEX IF NOT EXISTS idx_th_geom ON transit_hubs USING GIST(geom);
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_points (
                id TEXT PRIMARY KEY, geom GEOMETRY(Point, 4326) NOT NULL,
                name TEXT, point_type TEXT
            ); CREATE INDEX IF NOT EXISTS idx_sp_geom ON security_points USING GIST(geom);
        """)

        # Seed all data
        await seed_streetlights(conn)
        await seed_crimes(conn)
        await seed_businesses(conn)
        await seed_safe_havens(conn)
        await seed_cctv_zones(conn)
        await seed_transit_hubs(conn)
        await seed_security_points(conn)

        print("\n" + "=" * 60)
        print("✅ Jaipur 12-factor data seeding complete!")
        print("   💡 Streetlights  |  🚨 Crime  |  🏪 Businesses")
        print("   🏛️ Safe Havens   |  📹 CCTV   |  🚌 Transit")
        print("   🔐 Security Pts  |  ⚠️ Danger Pins (user-generated)")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
