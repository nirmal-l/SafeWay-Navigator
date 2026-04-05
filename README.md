# SafeWay Navigator

🔗 **Live Deployment:** [https://safe-way-navigator-b66txttpr-nirmal-ls-projects.vercel.app/]

SafeWay Navigator is a pedestrian routing engine built for Jaipur that prioritizes physical and psychological safety over simple speed. Instead of blindly routing users down the fastest dark alley, it guides them through well-lit, populated, and structurally safe streets.

## Why I Built This
Current navigation apps are fundamentally blind to context. My goal was to create a tool that calculates routes specifically for vulnerable pedestrians walking alone at night. 

To achieve this, I avoided just wrapping standard navigation APIs. Instead, the architectural core of this project is a custom pathfinding engine running over a geospatial network.

## Technical Implementation

### Core Logic & Data Structures
The routing engine uses a custom **A* Pathfinding Algorithm** traversing a `NetworkX` graph. Edges are weighted by a proprietary **12-Factor Penalty System** rather than purely distance. The algorithm calculates dynamic penalties based on localized factors like street lighting, crime hotspots, CCTV density, and active businesses.

To handle real-time spatial calculations efficiently, I utilize `scipy.spatial.cKDTree` for sub-millisecond nearest-neighbor lookups, rather than relying on heavy brute-force Haversine calculations.

### Data Strategy
To thoroughly test my logic, I built a comprehensive synthetic suite. Real Jaipur road topology is fetched live via `OSMnx`. Over this real-world grid, I seeded a **PostGIS** spatial database with high-quality proxy data (simulating specific crime zones, unlit streets, and safe havens) to reliably mimic a sprawling, unpredictable metropolitan landscape.

### Reliability
The project utilizes a split-stack architecture (`Vite/React` + `FastAPI`). Heavy spatial graph generation is pickled and cached to ensure the routing engine adheres to strict production memory limits (512MB RAM). On the client, IndexDB caches map states to ensure the core navigation survives cellular drops.

## Key Features
- **Dynamic Safe Routing:** Calculates and compares the top 3 safest pathing alternatives.
- **Virtual Guardian AI:** A hands-free, Gemini-powered continuous voice companion that provides psychological grounding and distraction for anxious walkers.
- **SOS Modules:** Includes a simulated "Fake Phone Call" interface and 1-tap live WebSocket location sharing.

## Alternatives Considered & Future Scope
While building the SafeWay Navigator, I considered several different ranking heuristics that I leaned away from due to data availability. However, moving forward, the **future of this project** involves adding a completely new dynamic metric: **Cellular Network Density**. 

Inspired by the offline crowd-status features of the application *"Where is my train"*, my next architectural goal is to passively interface with nearby network cell towers. By determining how many mobile devices are actively pinging a specific tower, a real-time **Cellular Network Density Heatmap** will be generated and directly fed into the graph algorithm. Paths intersecting with "hot" zones on this heatmap indicate active crowds and "eyes on the street" (even without CCTV or infrastructure), translating directly to a significantly higher dynamic safety score for night pedestrians.

---

## Local Setup Guide

The project is split into a frontend UI (`frontend`) and a Python routing engine (`backend`).

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for PostGIS)

### API Keys Configuration
To run the project locally, you will need to generate the following free API keys and place them in your `.env` file:

| Environment Variable | Where to Generate | Why it's needed |
| :--- | :--- | :--- |
| `VITE_MAPBOX_TOKEN` | [account.mapbox.com](https://account.mapbox.com) | Core map rendering and visualization. |
| `VITE_GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Powers the Relief Guardian AI voice companion. |
| `GOOGLE_PLACES_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) | Fetches dynamic real-time business hours logic. |
| `MAPBOX_TRAFFIC_TOKEN` | [account.mapbox.com](https://account.mapbox.com) | Same URL as map token. Pulls live traffic congestion for rating safety. |

### 1. Configure Keys & Database
1. Copy `.env.example` to a new file named `.env` and paste in your Mapbox and Gemini API keys. 
2. Start the database container:
```bash
docker compose up -d postgres
```

### 2. Generate Environment & Start Backend
Open a new terminal and prepare the Python environment:
```bash
cd backend

# Create and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database with proxy spatial data (Run this once)
python3 data/seed.py

# Start the routing API
python3 -m uvicorn main:app --reload --port 8000
```
*(Note: The very first route request triggers heavy graph pre-processing which takes ~60 seconds. Subsequent requests are instant).*

### 3. Start Frontend
Open a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** to view the app.
