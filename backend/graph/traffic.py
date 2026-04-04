import math
import random
import os
import httpx

MAPBOX_TOKEN = os.environ.get("MAPBOX_TRAFFIC_TOKEN", "") or os.environ.get("VITE_MAPBOX_TOKEN", "")

async def get_live_traffic_data(coordinates: list, vehicle_type: str, total_distance_m: float):
    """
    Calls Mapbox Directions API for live traffic OR simulates traffic and speed
    if external API fails or for non-driving modes.
    """
    # 1. Base commute time calculations (Fallback)
    # Walk: 5 km/h (1.38 m/s)
    # Bike: 35 km/h (9.72 m/s)
    # Drive: 25 km/h (6.94 m/s)
    
    speed_m_s = 1.38
    if vehicle_type == "bike":
        speed_m_s = 9.72
    elif vehicle_type == "drive":
        speed_m_s = 6.94
        
    base_duration_min = round(total_distance_m / speed_m_s / 60, 1)

    # Walkers don't have traffic. Bikes weave through traffic (mostly normal).
    if vehicle_type != "drive":
        return {
            "duration_min": base_duration_min,
            "congestion": ["low"] * (len(coordinates) - 1),
            "coordinates": coordinates
        }

    # 2. External API for Drive mode (Live Traffic)
    if MAPBOX_TOKEN:
        # Downsample to max 24 waypoints for Mapbox Directions API constraint
        if len(coordinates) <= 24:
            sampled = coordinates
        else:
            step = len(coordinates) / 23.0
            sampled = [coordinates[int(i * step)] for i in range(23)]
            sampled.append(coordinates[-1])
            
        waypoints = ";".join([f"{lon},{lat}" for lon, lat in sampled])
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{waypoints}?annotations=congestion,duration&overview=full&geometries=geojson&access_token={MAPBOX_TOKEN}"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json()
                    route = data["routes"][0]
                    live_duration_min = round(route["duration"] / 60, 1)
                    live_coords = route["geometry"]["coordinates"]
                    
                    # Flatten congestion array which is returned per-leg
                    live_congestion = []
                    for leg in route["legs"]:
                        ann = leg.get("annotation", {})
                        cong = ann.get("congestion", [])
                        live_congestion.extend(cong)
                        
                    # Handle edge case where annotations length doesn't perfectly match
                    while len(live_congestion) < len(live_coords) - 1:
                        live_congestion.append("low")
                        
                    return {
                        "duration_min": live_duration_min,
                        "congestion": live_congestion,
                        "coordinates": live_coords
                    }
        except Exception as e:
            print(f"Mapbox API fallback: {str(e)}")

    # 3. Simulation Fallback (if API fails or no token)
    # Simulate patches of traffic for drive
    simulated_congestion = []
    
    # Generate realistic patches of traffic
    current_state = "low"
    states = ["low", "moderate", "heavy"]
    weights = [0.7, 0.2, 0.1]
    
    for _ in range(len(coordinates) - 1):
        if random.random() < 0.15: # 15% chance to change traffic state per segment
            current_state = random.choices(states, weights=weights)[0]
        simulated_congestion.append(current_state)
        
    # Penalty to duration if heavy traffic
    heavy_count = simulated_congestion.count("heavy")
    moderate_count = simulated_congestion.count("moderate")
    traffic_penalty_min = (heavy_count * 0.5) + (moderate_count * 0.2)
    
    return {
        "duration_min": round(base_duration_min + traffic_penalty_min, 1),
        "congestion": simulated_congestion,
        "coordinates": coordinates
    }
