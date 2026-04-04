# 🧠 Context — Fear-Free Night Navigator
## For Future LLM Sessions: Read This First

This document captures all architectural decisions, gotchas, and living context so future LLM sessions don't hallucinate or repeat solved problems.

---

## Project Identity

| Field | Value |
|-------|-------|
| **Project Name** | Fear-Free Night Navigator |
| **Target City** | Jaipur, Rajasthan, India |
| **Stack** | Python FastAPI + React Vite + PostgreSQL PostGIS + Mapbox GL JS |
| **Bounding Box** | `[26.7800, 75.7000, 27.0200, 75.9000]` (S lat, W lng, N lat, E lng) — covers central Jaipur |
| **Port — Backend** | `8000` |
| **Port — Frontend** | `5173` |
| **Port — PostGIS** | `5433` (host) → `5432` (container) |
| **Safety Engine** | v2.0 — 12-Factor Weighted Scoring |

---

## Why Python for Backend (Not Node.js)

The problem statement suggests Node.js/Express, but **we chose Python FastAPI** deliberately:
- `OSMnx` library (Python-only) auto-downloads OpenStreetMap road graphs as NetworkX graph objects
- `NetworkX` has a native `astar_path()` function — we don't need to write graph traversal code
- `GeoPandas` + `Shapely` handle spatial joins in 3 lines vs. hundreds of lines in JS
- **Decision is final — do not suggest switching to Node.js**

---

## Why Mapbox GL JS (Not Google Maps)

- Google Maps does NOT allow custom routing weights — you cannot inject your own safety score into their routing engine
- Mapbox allows drawing fully custom polylines from any coordinate array returned by our backend
- Mapbox has a generous free tier (50,000 loads/month)
- Mapbox supports custom dark-mode map styles out of the box (critical for a "night navigation" product)
- **Decision is final — do not suggest switching to Google Maps**

---

## Graph Architecture

```
Graph G = OSMnx graph of Jaipur central zone
Nodes = Road intersections (each has lat/lng)
Edges = Road segments between intersections
Edge properties:
  - length            (meters, from OSM)
  - name              (street name, from OSM)
  - road_type         (OSM highway tag: primary, residential, service, etc.)
  - custom_weight     (our safety-adjusted weight — higher = less safe)
  - streetlight_count
  - crime_count
  - danger_pin_count
  - safe_haven_count
  - cctv_count
  - transit_hub_count
  - security_count
  - business_count
```

The graph is built once on backend startup and cached to `backend/data/jaipur_graph.pkl`. Rebuilding takes ~60-90 seconds (OSM network download). The pickle is gitignored but should be committed for hackathon demos.

---

## Data Architecture (PostGIS — 8 Tables)

| Table | Purpose | Key Columns |
|---|---|---|
| `streetlights` | Lighting infrastructure | `geom`, `source` |
| `crime_records` | Historical crime hotspots | `geom`, `category`, `severity` |
| `businesses` | Commercial activity (with hours) | `geom`, `closing_hour`, `open_late` |
| `danger_pins` | Crowdsourced real-time warnings | `geom`, `category`, `expires_at` |
| `safe_havens` | Police stations, hospitals, fire stations | `geom`, `category`, `is_24x7` |
| `cctv_zones` | Surveillance camera locations | `geom`, `camera_count` |
| `transit_hubs` | Bus terminals, auto stands, metro stations | `geom`, `hub_type`, `is_24x7` |
| `security_points` | ATMs, hotels, gated societies | `geom`, `point_type` |

**Key PostGIS query pattern (spatial join):**
```sql
SELECT COUNT(*) as cnt 
FROM streetlights 
WHERE ST_DWithin(geom::geography, ST_MakePoint($lon, $lat)::geography, 10);
```
`ST_DWithin` with `::geography` cast gives distance in meters (not degrees).

---

## Jaipur Data Context

### Seeded Crime Hot Zones (realistic, not real)
- **Hawa Mahal / Badi Chaupar** — Dense tourist crowds, pickpocketing
- **Sindhi Camp / Jaipur Junction** — Budget hotels, transit chaos
- **Sikar Road Industrial** — Isolated stretches, elevated crime
- **Jagatpura Outskirts** — Dark developing areas

### Safe Corridors (high safety weights)
- **MI Road / Panch Batti** — Best-lit commercial hub
- **C-Scheme** — Upscale, security presence
- **JLN Marg** — Smart City corridor with CCTV, always busy
- **Malviya Nagar / Gaurav Tower** — Well-maintained, lit

---

## Frontend State Management

No Redux. Uses React Context + custom hooks:
- `useRouting()` — manages route API calls and result state
- `useGeolocation()` — manages real-time GPS
- `useDangerPins()` — manages pins WebSocket/polling
- Navigation mode: `isNavigating` state in `App.jsx`

---

## Known Gotchas & Decisions

### 1. OSMnx Download Latency
First run downloads Jaipur road data. Subsequent runs use the pickle cache. If the pickle is missing, the backend starts with a 60-90 second cold start. **Always commit the pickle for demos.**

### 2. PostGIS Distance Units
NEVER use `ST_DWithin(geom, point, distance_meters)` without `::geography` cast.

### 3. Mapbox Token Exposure
The Mapbox token goes in `VITE_MAPBOX_TOKEN` which is exposed to the browser (by Vite design). This is normal.

### 4. A* vs Dijkstra's
We use A* with a geographic heuristic (straight-line distance) — 3-5x faster than Dijkstra's on large road networks.

### 5. Coordinate Convention
**ALWAYS** store as `(latitude, longitude)` in Python/DB. **ALWAYS** pass to Mapbox as `[longitude, latitude]`. This is the #1 source of "pin in the ocean" bugs.

### 6. Graph Cache Invalidation
If you change the bounding box, scoring algorithm, or edge attributes, **delete `backend/data/jaipur_graph.pkl`** to force rebuild.

---

## How to Start (Quick Reference)

```bash
# 1. Start database
docker compose up -d

# 2. Start backend
cd backend
pip install -r requirements.txt
python data/seed.py           # seeds all 8 tables
python -m uvicorn main:app --reload --port 8000

# 3. Start frontend
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```
