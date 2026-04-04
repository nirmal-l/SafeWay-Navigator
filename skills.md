# 🔧 Skills — Fear-Free Night Navigator

Technical patterns, conventions, and reference snippets for development.

---

## Safety Score Tuning (v2.0 — 12-Factor Engine)

All constants are defined in `backend/graph/safety_scorer.py`.

### Tier 1 — Infrastructure & Urban Design

| Constant | Default | Effect of Increasing |
|----------|---------|---------------------|
| `STREETLIGHT_BONUS` | 0.5 | Routes prefer more streetlights |
| `SAFE_HAVEN_BONUS` | 4.0 | Routes strongly prefer paths near police/hospitals |
| `CCTV_BONUS` | 3.0 | Routes prefer surveilled corridors |
| `ROAD_HIERARCHY` | dict | Primary roads score better than alleys |
| `DEFAULT_ROAD_PENALTY` | 2.0 | Unknown road types get mild penalty |

### Tier 2 — Dynamic & Temporal

| Constant | Default | Effect of Increasing |
|----------|---------|---------------------|
| `BUSINESS_BONUS_FULL` | 1.5 | Routes prefer paths with open businesses |
| `BUSINESS_BONUS_CLOSING` | 0.75 | Reduced bonus within 1hr of closing |
| `DARK_NIGHT_PENALTY` | 25.0 | Routes strongly avoid dark roads at night |
| `PEAK_DANGER_MULTIPLIER` | 1.3 | All penalties amplified 10PM–2AM |

### Tier 3 — Micro-Level & Community

| Constant | Default | Effect of Increasing |
|----------|---------|---------------------|
| `CRIME_PENALTY` | 5.0 | Routes strongly avoid crime zones |
| `DANGER_PIN_PENALTY` | 10.0 | Routes immediately avoid user-flagged areas |
| `TRANSIT_HUB_BONUS` | 2.0 | Routes prefer bus stops, auto stands |
| `SECURITY_POINT_BONUS` | 1.5 | Routes prefer ATMs/hotels (guard presence) |

---

## A* Custom Weight Pattern

```python
# In pathfinder.py — always use "custom_weight" as the edge attribute
path = nx.astar_path(
    G, source=start, target=end,
    heuristic=lambda u, v: _haversine_heuristic(u, v, G),
    weight="custom_weight",
)
```

---

## PostGIS Spatial Query Pattern

```sql
-- Find features within N meters of a coordinate
SELECT * FROM streetlights
WHERE ST_DWithin(
    geom::geography,
    ST_MakePoint($lng, $lat)::geography,
    10  -- radius in meters
);
```

**CRITICAL:** Always cast to `::geography` for meter-based distance. Without it, PostGIS uses degrees (10 degrees ≈ 1,110 km).

---

## OSMnx Graph Building

```python
import osmnx as ox
G = ox.graph_from_bbox(
    bbox=(north, south, east, west),
    network_type="walk",
    simplify=True,
)
G = ox.distance.add_edge_lengths(G)
```

Edge attributes from OSM:
- `length` (meters)
- `highway` (road classification: primary, residential, service, etc.)
- `name` (street name, can be list)
- `geometry` (Shapely LineString, if not simplified)

---

## Mapbox Layer Naming Convention

All Mapbox GL JS layers use the `ffnn-` prefix:
```javascript
map.addSource('safe-routes', { type: 'geojson', ... });
map.addLayer({ id: 'ffnn-safe-route', ... });
map.addLayer({ id: 'ffnn-alt-routes', ... });
map.addLayer({ id: 'ffnn-route-glow', ... });
```

---

## Data Seeding Pattern

When adding new seed data to `backend/data/seed.py`:

```python
# Always use upsert to allow re-running the seed safely
await conn.execute("""
    INSERT INTO streetlights (id, geom, source)
    VALUES ($1, ST_MakePoint($2, $3), $4)
    ON CONFLICT (id) DO NOTHING
""", uid, lng, lat, source)
```

---

## Environment Variable Rules

| Context | Convention | Example |
|---------|-----------|---------|
| Backend Python | `UPPERCASE_SNAKE_CASE` | `DATABASE_URL` |
| Frontend Vite | `VITE_` prefix required | `VITE_MAPBOX_TOKEN` |
| Docker Compose | Same as backend | `POSTGRES_PASSWORD` |

**Never hardcode any token in source code.** Always use `os.getenv("VAR_NAME")` in Python and `import.meta.env.VITE_VAR_NAME` in Vite/React.

---

## Git Rules

```
.gitignore must include:
  backend/data/jaipur_graph.pkl   ← large binary, regenerated on start
  .env                             ← NEVER commit real env file
  __pycache__/
  node_modules/
  dist/
```

---

## Running the Project (Developer Reference)

```bash
# Full fresh start
docker compose up -d                      # Start PostGIS
cd backend && pip install -r requirements.txt
python data/seed.py                       # Seed all 8 tables
uvicorn main:app --reload --port 8000     # Start backend

# New terminal
cd frontend && npm install && npm run dev # Start frontend
# → http://localhost:5173
```

---

## Testing a Route (cURL)

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{
    "start": [26.9239, 75.8267],
    "end": [26.8967, 75.8288]
  }'
```
Expected: Array of 3 route objects with `safety_score`, `coordinates`, `safe_haven_count`, `cctv_segments`, `transit_nearby`, and `road_quality`.
