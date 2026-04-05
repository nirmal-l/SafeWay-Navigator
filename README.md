# 🛡️ SafeWay Navigator — Jaipur

> AI-powered pedestrian safety routing engine prioritizing **psychological and physical safety** over speed. Because the fastest route is not always the safest route.

**City:** Jaipur, Rajasthan | **Stack:** Python FastAPI + React + PostgreSQL/PostGIS + Mapbox GL JS

---

## 🧭 About The Project

Standard GPS applications (like Google Maps or Apple Maps) optimize entirely for speed and shortest distance, while acting blind to external safety conditions. A route cutting through a dark, isolated alley might be 2 minutes faster, but can be psychologically threatening—especially for women, elderly users, or solo pedestrians walking at night.

**SafeWay Navigator** flips this paradigm. We measure and calculate paths using a hyper-localized **12-factor safety metric** that dynamically assesses street lighting, crime records, active community danger pins, open commercial hubs, and overall structural safety to guide users safely through the night.

---

## 🌟 Core Functionalities & Features

### 1. 🧮 AI Safe Route Generation (A* Pathfinder)
At the core of the navigator is a robust A* (A-Star) Pathfinding engine. Instead of using distance, it utilizes a deeply weighted "Safety Penalty Network". 
- When calculating a route, we generate the **Top 3 Safest Alternatives**. 
- The UI presents detailed route cards comparing ETA, Distances, and the crucial **Safety Score (0-100)**.
- Safe route polygons visually glow in real-time on the map denoting varying traffic levels and route safety dynamically.

### 2. ⚡ The 12-Factor Dynamic Safety Score
Roads are evaluated contextually based on their geographical metadata:
- **Infrastructure & Urban Design:** Streetlight coverage, Road Size / Hierarchy, Proximity to Police/Hospitals (Safe Havens), and CCTV Zones.
- **Dynamic & Temporal Dimensions:** Deep Night Penalty (heavily penalizing unlit roads from 6 PM to 6 AM), Peak Danger Time Identifiers (factors multiply severely between 10 PM and 2 AM), and Commercial Activity Drop-offs as stores close.
- **Micro-Level Community Factors:** Verified historical Crime Hotspots, real-time Community Danger Pins, proximity to Transit Hubs/ATMs/Hotels.

### 3. 🎧 Relief Virtual Guardian (AI Companion)
- A Gemini-powered empathetic voice companion activated during navigation.
- Push-to-talk interface with real-time speech recognition and TTS.
- Proactively engages users with conversation, questions, and immersive storytelling to provide psychological grounding during solo night walks.

### 4. ✨ Premium Adaptive UI Dashboard
- **Glassmorphism UI:** Complete dark-mode minimal architecture reducing eye strain at night.
- **Live System Telemetry:** Top dashboard provides real-time system metrics, nearby app users, localized ambient light conditions, and visibility percentages.
- **Navigational Fluidity:** Smooth CSS animations mapped with React states to keep the application responsive and interactive.

### 5. 🚨 Integral SOS Protocols
Designed for split-second emergency responses, placing a floating SOS interaction button inside live navigational sessions:
- **Simulated Fake Call:** Provides an interactive interface mimicking a real phone call from a "Guardian," paired with a scrolling 3-line script prompt to deter harassment. 
- **Share Guardian Link:** Quickly syncs your live WebSocket location marker through an anonymized browser URL.
- **Direct Emergency Dispatch:** 1-tap fast connection to dialing National Emergency Services (112).

### 6. 👥 Crowdsourced Danger Pins (Social Features)
Street conditions evolve faster than datasets. We let the community guide the map:
- Users can drop customizable warning pins directly on the map surface (e.g., *Broken Streetlights, Aggressive Stray Dogs, Suspicious Loitering, Damaged Footpaths*).
- These pins actively integrate into the A* Graph Pathfinder and immediately lower the path safety rating for an active 24-hour decay timeframe. 

### 7. 🔌 Offline-First Resiliency
- Built-in `OfflineRouter` logic syncing the whole Map Routing Mesh network into the system directly. 
- Designed explicitly for situations in tight urban areas where cellular data and internet connectivity drop to zero.

---

## 🛠️ Technical Architecture

```text
+------------------+        +-------------------+        +--------------------+
|   React Frontend |  HTTP  |   Python FastAPI   | SQL    |  PostgreSQL+PostGIS|
|   (Vite + Mapbox)|<------>|   Backend Server   |<------>|  (Docker Container)|
+------------------+        +-------------------+        +--------------------+
                                      |
                              +-------+--------+
                              |  NetworkX Graph |
                              | (A* Pathfinder) |
                              +----------------+
                                      |
                         +------------+------------+
                         |                         |
                  +------+------+          +-------+-------+
                  | OpenStreetMap|          | Jaipur Safety |
                  |  (OSMnx)    |          | Data (8 tables)|
                  +-------------+          +---------------+
```

---

## 🏃‍♂️ Local Development (Quick Start)

### Prerequisites
- **Docker** (for PostgreSQL/PostGIS)
- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **API Keys** (see below)

### Step 1: Get Your API Keys (Free)

| Key | Where to Get | Required? |
|-----|-------------|-----------|
| `VITE_MAPBOX_TOKEN` | [mapbox.com](https://account.mapbox.com) — create a free account, copy your default public token (`pk.ey...`) | ✅ Yes |
| `VITE_GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/) — create API key | For Relief Guardian |
| `GOOGLE_PLACES_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) — enable Places API | Optional |

### Step 2: Configure Environment

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/SafeWay-Navigator.git
cd SafeWay-Navigator

# Create your local environment file
cp .env.example .env

# Open .env and paste your API keys
# At minimum, fill in VITE_MAPBOX_TOKEN
```

### Step 3: Start the Database

```bash
docker compose up -d postgres
# Wait ~10 seconds for PostGIS to initialize
```

### Step 4: Start the Backend

```bash
cd backend
pip install -r requirements.txt
python3 data/seed.py             # Seeds 8 safety data tables (only needed once)
python3 -m uvicorn main:app --reload --port 8000
```

> **Note:** On first request, the graph engine will download the Jaipur road network from OpenStreetMap (~60-90 seconds, needs ~800MB RAM). Subsequent starts load from cache instantly.

### Step 5: Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the map should load and routing should work!

---

## 🚀 Production Deployment

This app deploys as a **split-stack**: Backend on **Render**, Frontend on **Vercel**.

See **[deploy.md](deploy.md)** for the full step-by-step deployment guide.

### Quick Reference

| Component | Platform | Root Directory | Key Env Vars |
|-----------|----------|---------------|--------------|
| PostgreSQL | Render (Free PostgreSQL) | — | Auto-generated |
| Backend | Render (Web Service) | `backend` | `DATABASE_URL`, `MAPBOX_TRAFFIC_TOKEN` |
| Frontend | Vercel | `frontend` | `VITE_MAPBOX_TOKEN`, `VITE_BACKEND_URL`, `VITE_GEMINI_API_KEY` |

---

## 💡 How to Use (Workflows)

Once the application is running at `http://localhost:5173`, here are the core workflows you can experience:

### Workflow 1: Finding a Safe Route
1. Look at the **"SafeWay Navigator" Search Panel** on the left.
2. Enter your current location and your destination (e.g., from "Hawa Mahal" to "MI Road").
3. Select your travel mode (Walk, Bike, or Car).
4. Click **Calculate Safe Route**. The system will scan the 12-factor penalty network and render the Top 3 safest paths.
5. Click on the generated route cards to toggle their corresponding glowing polygons on the map. Notice the Safety Score differences!

### Workflow 2: Reporting a Danger Zone
1. Is a streetlamp broken, or you spotted suspicious activity? 
2. Click directly on that spot on the **Mapbox interface**.
3. A modal will pop up. Select the category (e.g., `Broken Light` or `Suspicious`).
4. Submit the pin. The pathfinder will immediately register this danger zone and dynamically reroute paths around it for the next 24 hours.

### Workflow 3: Activating SOS & Fake Call
1. Start navigating a selected route by clicking **Start Journey**.
2. Notice the large glowing Red **SOS Button** at the bottom right. Click it.
3. A Safety Options menu will appear.
4. Click **Fake Phone Call**. A simulated "Incoming Call from Guardian" interface will take over the screen with a scrolling script you can read out loud to deter harassment.

### Workflow 4: Relief Virtual Guardian
1. While navigating, tap the **Relief** button.
2. Tap the glowing orb and speak — the AI companion will respond with calming conversation.
3. It proactively asks questions and tells immersive stories to keep you distracted from anxiety.

---

## 📡 API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/route` | Returns Top 3 generated safe routes and coordinates |
| `GET` | `/api/danger-pins` | Retrieves current crowdsourced warning zones |
| `POST` | `/api/danger-pins` | Submits a spatial local warning pin |
| `GET` | `/api/stats/overview` | Returns aggregate counts of all active safety data layers |
| `GET` | `/docs` | Fully interactive FastAPI Swagger documentation interface |
| `WS` | `/ws/safety` | Real-time Safety Mesh (danger pin broadcasts, live location) |
| `WS` | `/ws/guardian/{token}` | Guardian Observer live location tracking |

See [api.md](api.md) for deeper information regarding map-related tokens and external API Integrations.
