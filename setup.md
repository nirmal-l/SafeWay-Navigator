# 🛠️ Installation & Setup Guide

Welcome to the **Fear-Free Night Navigator** setup guide! This document explains how to get the project running locally across different operating systems (macOS, Windows, Linux).

---

## 📋 Prerequisites

Before you start, ensure your system has the following installed:

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Used to run PostgreSQL + PostGIS)
2. **[Python 3.9+](https://www.python.org/downloads/)**
3. **[Node.js 18+](https://nodejs.org/en/)** and `npm`
4. **Mapbox Account**: You'll need a free token from [mapbox.com](https://account.mapbox.com/) to render the maps.

---

## 💻 OS-Specific Prerequisites

### 🍏 macOS
If you use [Homebrew](https://brew.sh/), you can install the dependencies easily:
```bash
brew install python node docker
brew install --cask docker
```

### 🪟 Windows
1. We highly recommend using **WSL2 (Windows Subsystem for Linux)**.
2. Install **Docker Desktop** and enable the "WSL2 based engine" in the settings.
3. Open your WSL terminal (e.g., Ubuntu) and install Python and Node:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nodejs npm
   ```

### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm docker.io docker-compose
sudo systemctl enable --now docker
```

---

## 🚀 Step-by-Step Installation

### 1. Clone & Configure Environment

First, duplicate the environment variables template file to configure your local instances:

```bash
cd project
cp .env.example .env
```

Open `.env` in a text editor and add your **Mapbox Token**:
```env
VITE_MAPBOX_TOKEN=pk.eyJ1Ijoi...  # Paste your token here
```

*(For more advanced API configurations, check `api.md`)*

### 2. Start the PostGIS Database

Our geographical data lives in a PostgreSQL database enriched with PostGIS. To start it:

```bash
# This starts the database container in detached mode
docker compose up -d
```
> **Note:** The database binds to port **5433**. Make sure this port is free on your host machine.

### 3. Setup the Python Backend

The backend engine handles the A* Pathfinding graph and safety scores.

```bash
cd backend

# Install required Python packages
pip3 install -r requirements.txt

# Seed the geographic and safety data into the database (Only run this ONCE)
python3 data/seed.py

# Start the FastAPI Server
python3 -m uvicorn main:app --reload --port 8000
```
> **First Startup Warning:** The very first time you boot the API, it downloads the Jaipur OSM road network (~60-90 seconds). Subsequent starts will load a cached version instantly.

### 4. Setup the React Frontend

The beautifully designed dashboard and map UI runs on Vite & React. Open a **new terminal tab**:

```bash
cd project/frontend

# Install node modules
npm install

# Start the development server
npm run dev
```

The terminal will provide a local URL (usually **http://localhost:5173**). Open this in your browser to start navigating the dark streets of Jaipur safely!

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| Map shows "Mapbox Token Required" | Make sure `VITE_MAPBOX_TOKEN` is saved in your `.env` file correctly. |
| Backend is slow on the first start | Normal behavior. It is downloading routing graph data. It will be cached for future runs. |
| Database connection error | Ensure Docker Desktop is running and you ran `docker compose up -d`. Verify port 5433 availability. |
| Safety scores all show 100 | You forgot to run `python3 data/seed.py`. This populates the 8 safety parameter tables. |
| Routing Graph is stale | Delete the cached file `backend/data/jaipur_graph.pkl` and restart the Uvicorn backend. |
