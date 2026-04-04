"""
OpenStreetMap (OSM) Overpass API Data Fetcher

This script demonstrates how to fetch live, real-world safety data
directly from OpenStreetMap without needing any API keys (like Yelp).
It queries the Overpass API for Jaipur's bounding box.

You can use this data to dynamically augment your PostgreSQL seeds.
"""
import requests
import json

# Jaipur approximate bounding box: South, West, North, East
JAIPUR_BBOX = "26.6800,75.6000,27.1200,76.0000"

def fetch_osm_data(query_tag: str):
    """
    Fetch nodes with a specific OSM tag within Jaipur using Overpass API.
    query_tag example: 'amenity=police' or 'highway=street_lamp'
    """
    print(f"📡 Fetching live OSM data for: {query_tag}...")
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Overpass Query Language (QL)
    # [out:json]; node["amenity"="police"](bbox); out;
    key, value = query_tag.split("=")
    overpass_query = f"""
    [out:json];
    node["{key}"="{value}"]({JAIPUR_BBOX});
    out center;
    """
    
    try:
        response = requests.post(overpass_url, data={'data': overpass_query})
        response.raise_for_status()
        data = response.json()
        
        results = []
        for element in data.get('elements', []):
            if element['type'] == 'node':
                tags = element.get('tags', {})
                results.append({
                    "lat": element.get('lat'),
                    "lon": element.get('lon'),
                    "name": tags.get('name', 'Unknown'),
                })
        
        print(f"✅ Found {len(results)} {query_tag} nodes in Jaipur.")
        return results
    except Exception as e:
        print(f"❌ Error fetching from OSM: {e}")
        return []

if __name__ == "__main__":
    print("🌍 Fear-Free Night Navigator: Live OSM Data Integration")
    print("-" * 50)
    
    # Example 1: Fetch Police Stations (Safe Havens)
    police = fetch_osm_data("amenity=police")
    if police:
        print(f"Sample Police Station: {police[0]['name']} at ({police[0]['lat']}, {police[0]['lon']})")
    print()

    # Example 2: Fetch Hospitals (Safe Havens)
    hospitals = fetch_osm_data("amenity=hospital")
    if hospitals:
        print(f"Sample Hospital: {hospitals[0]['name']} at ({hospitals[0]['lat']}, {hospitals[0]['lon']})")
    print()
    
    # Example 3: Fetch ATMs (Security presence)
    atms = fetch_osm_data("amenity=atm")
    if atms:
        print(f"Sample ATM: {atms[0]['name']} at ({atms[0]['lat']}, {atms[0]['lon']})")
        
    print("-" * 50)
    print("💡 To use this data, you would parse these coordinates and insert them into your POSTGIS tables!")
