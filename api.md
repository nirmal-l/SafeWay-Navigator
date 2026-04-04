# 🔑 Fear-Free Night Navigator — API Keys & Data Sources

## Overview

The Night Navigator uses a **12-factor safety scoring engine** that pulls data from multiple sources. The system works **fully offline** with seeded Jaipur data, but optional API keys unlock real-time intelligence.

---

## Required Keys (1)

### 1. Mapbox GL JS Token
| | |
|---|---|
| **Variable** | `VITE_MAPBOX_TOKEN` |
| **Required?** | ✅ YES — the map will not render without this |
| **Cost** | Free tier: 50,000 map loads/month |
| **Get it at** | [https://account.mapbox.com/access-tokens/](https://account.mapbox.com/access-tokens/) |
| **Token format** | Starts with `pk.ey...` |

**What it powers:**
- Dark-mode satellite map rendering (`mapbox://styles/mapbox/navigation-night-v1`)
- Mapbox Geocoding API (search autocomplete for locations in Jaipur)
- GeoJSON route line rendering on the map
- Live GPS cursor tracking

**Setup:**
1. Create a free Mapbox account
2. Copy your **Default public token** from the dashboard
3. Paste it in your `.env` file:
   ```
   VITE_MAPBOX_TOKEN=pk.eyJ1Ijoi...
   ```

---

## Optional Keys (2)

### 2. Google Places API
| | |
|---|---|
| **Variable** | `GOOGLE_PLACES_API_KEY` |
| **Required?** | ❌ NO — seeded business data is used as fallback |
| **Cost** | Free tier: $200/month credit (~5,000 requests) |
| **Get it at** | [https://console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Enable "Places API" |

**What it unlocks:**
- Real-time business operating hours for Jaipur (replaces static seed data)
- Live "time-decay" commercial scoring — knows which shops are physically open right now
- Accurate late-night activity detection for the "eyes on the street" metric

**Without this key:** The system uses the seeded `businesses` table with pre-configured closing hours (e.g., markets close at 9PM, pharmacies are 24/7).

---

### 3. Mapbox Traffic API
| | |
|---|---|
| **Variable** | `MAPBOX_TRAFFIC_TOKEN` |
| **Required?** | ❌ NO — road hierarchy scoring is used as fallback |
| **Cost** | Included in Mapbox free tier |
| **Get it at** | Same Mapbox dashboard as your map token |

**What it unlocks:**
- Live traffic density data on Jaipur roads
- Roads with active vehicle flow score higher ("eyes on the street" via moving traffic)
- Completely dead/empty roads at 2AM get penalized

**Without this key:** Road safety is inferred from the OSM `highway` tag classification (primary roads score higher than service alleys).

---


## Free Data Sources (No API Key Required)

| Source | Data Provided | Used For |
|---|---|---|
| **OpenStreetMap (via OSMnx)** | Road network, road types, street names | Graph building, road hierarchy scoring |
| **OSM Overpass API** | Streetlight locations, amenities, POIs | Streetlight counts, business locations |
| **Seeded PostGIS Data** | 8 safety data tables | All 12 scoring factors |

---

## The 12-Factor Safety Score

| # | Factor | Data Source | Effect |
|---|---|---|---|
| 1 | Streetlights | OSM + Seeded | Lit streets get bonus |
| 2 | Road Hierarchy | OSM `highway` tag | Main roads preferred over alleys |
| 3 | Safe Havens | Seeded (police, hospitals) | Proximity to refuge = bonus |
| 4 | CCTV Zones | Seeded (Jaipur corridors) | Surveillance = bonus |
| 5 | Crime Records | Seeded | Crime hotspots penalized |
| 6 | Danger Pins | User-submitted (crowdsourced) | Real-time nuisance avoidance |
| 7 | Business Activity | Seeded + Google Places (optional) | Open businesses = safe |
| 8 | Time Decay | System clock | Closed shops lose their bonus |
| 9 | Dark Night Penalty | System clock | Unlit roads at night = heavy penalty |
| 10 | Peak Danger Window | System clock (10PM-2AM) | All penalties amplified ×1.3 |
| 11 | Transit Hubs | Seeded | Bus/auto/metro proximity = bonus |
| 12 | Manned Security | Seeded (ATMs, hotels) | Guard presence = bonus |
