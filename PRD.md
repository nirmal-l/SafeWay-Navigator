# 📋 Product Requirements Document (PRD)
## Fear-Free Night Navigator — Jaipur

**Version:** 2.0.0  
**Last Updated:** 2026-04-03  
**Target City:** Jaipur, Rajasthan, India

---

## 1. Problem Statement

Standard GPS applications (Google Maps, Apple Maps) optimize for speed and shortest distance. They are **blind to safety**. A route through a dark, isolated alley may be faster by 2 minutes but psychologically threatening — especially for women, elderly users, and solo pedestrians walking at night.

**The core insight:** Psychological safety ≠ Physical safety, but they are correlated. A well-lit road with open shops, CCTV surveillance, and no recent crime history makes a pedestrian *feel* safer and statistically *is* safer.

---

## 2. Target Users (Personas)

| Persona | Description |
|---------|-------------|
| 🚶‍♀️ **Priya, 24** | Working professional in C-Scheme, walks home from Metro at 11 PM |
| 👴 **Rajesh, 67** | Retired, evening walks near JLN Marg, concerned about poorly lit streets |
| 🧑‍🎓 **Arjun, 21** | College student near Raja Park, frequents late-night food joints |

---

## 3. Core Features (MVP)

### F1 — Safe Route Generation (Top 3)
- User inputs origin + destination (text search via Mapbox Geocoding or current location)
- Backend runs A* K-shortest-path algorithm with 12-factor safety-weighted road segments
- UI displays 3 route alternatives as selectable cards with safety metrics
- Route card shows: Distance, ETA, Safety Score (0-100), lit segments, safe havens, CCTV, transit, road quality

### F2 — 12-Factor Safety Score
- Tier 1: Streetlights, Road Hierarchy, Safe Havens, CCTV Zones
- Tier 2: Time-Decayed Commerce, Dark Night Penalty, Peak Danger Window (10PM–2AM)
- Tier 3: Crime Records, Danger Pins, Transit Hubs, Manned Security

### F3 — SOS / Fake Phone Call
- Floating SOS button visible during active navigation
- On tap: plays a realistic pre-recorded phone call audio
- Shows a modal with emergency contacts

### F4 — Guardian Live Link
- Auto-generate a shareable URL showing user's live location
- Link expires 4 hours after creation

### F5 — Community Danger Pins
- Long-press on map to drop a warning pin
- Categories: `Broken Light`, `Suspicious Activity`, `Aggressive Animal`, `Unsafe Footpath`, `Loitering`, `Other`
- Pins affect real-time safety score. Auto-expire after 24 hours.

### F6 — Live Navigation Mode
- "Start Journey" button locks map camera to GPS position
- Pulsing blue beacon follows user in real-time
- Alternative routes hidden during navigation for clarity
- Compact navigation overlay replaces full search panel

---

## 4. Technical Architecture

```
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

## 5. Safety Score Formula (12-Factor v2.0)

```
edge_weight = base_length_meters
             - (streetlights_within_10m × 0.5)         # Lighting bonus
             + ROAD_HIERARCHY[osm_highway_tag]          # Road type modifier
             - (safe_havens_within_100m × 4.0)          # Refuge bonus
             - (cctv_within_50m × 3.0)                  # Surveillance bonus
             - (business_activity × time_decay_factor)  # Commerce (decays after closing)
             + (crimes_within_50m × 5.0)                # Crime penalty
             + (danger_pins_within_20m × 10.0)          # Community warning
             - (transit_hubs_within_80m × 2.0)          # Transit bonus
             - (security_points_within_40m × 1.5)       # Manned security bonus
             + (is_night AND no_streetlight ? 25 : 0)   # Dark night penalty

If 10PM-2AM: all penalties × 1.3                        # Peak danger window
```

**Safety Score (displayed to user):**
```
score = 100 × (1 - (avg_weight - min_weight) / (max_weight - min_weight))
```
Score of 100 = perfectly safe. Score of 0 = avoid at all costs.

---

## 6. Data Sources

| Data | Source | Refresh Rate |
|------|--------|-------------|
| Road network + types | OpenStreetMap via OSMnx | On startup, cached |
| Streetlights | Seeded Jaipur data | Static (update weekly) |
| Crime hot zones | Seeded Jaipur data | Static for hackathon |
| Businesses (with hours) | Seeded + Google Places API (optional) | Static / Real-time |
| Safe havens | Seeded Jaipur data (police, hospitals, fire) | Static |
| CCTV zones | Seeded Jaipur Smart City data | Static |
| Transit hubs | Seeded Jaipur data | Static |
| Security points | Seeded Jaipur data (ATMs, hotels) | Static |
| Danger pins | User-submitted via app | Real-time |

---

## 7. Non-Functional Requirements

- Route must compute in < 3 seconds for any two points within Jaipur's central zone
- Map must render at 60fps on mid-range Android devices
- App must work without internet for 30 seconds (cached route)
- Guardian link must work for viewers without the app installed

---

## 8. Out of Scope (v1.0)

- Turn-by-turn voice navigation
- Integration with public transit (RSRTC buses)
- User accounts / authentication
- Paid features
