import sys
import json
import random
from pathlib import Path
import networkx as nx

sys.path.append(str(Path(__file__).parent.parent))

from graph.builder import get_graph, apply_safety_weights, JAIPUR_BBOX
from data.seed import (
    STREETLIGHT_CLUSTERS, CRIME_CLUSTERS, BUSINESSES,
    SAFE_HAVENS, CCTV_ZONES, TRANSIT_HUBS, SECURITY_POINTS
)

def export_graph_to_json(G: nx.MultiDiGraph, output_file: str):
    print("Serializing graph nodes...")
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": str(node_id),
            "data": {
                "lng": data["x"],
                "lat": data["y"]
            }
        })

    print("Serializing graph edges and safety metrics...")
    links = []
    for u, v, key, data in G.edges(keys=True, data=True):
        links.append({
            "fromId": str(u),
            "toId": str(v),
            "data": {
                "weight": data.get("custom_weight", 10.0),
                "dist": data.get("length", 10.0),
                "sh": data.get("safe_haven_count", 0),
                "lit": 1 if data.get("streetlight_count", 0) > 0 else 0
            }
        })

    output_data = {
        "nodes": nodes,
        "links": links
    }

    print(f"Writing to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(output_data, f)
    
    size_mb = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"Success! Scalable Graph JSON Exported: {size_mb:.2f} MB")
    print(f"Total Nodes: {len(nodes)} | Total Links: {len(links)}")


def _generate_layer(clusters, density_index, is_crime=False):
    data = []
    for row in clusters:
        lat = row[0]
        lng = row[1]
        density = row[density_index]
        for _ in range(density):
            dlat = random.uniform(-0.003, 0.003)
            dlng = random.uniform(-0.003, 0.003)
            item = {"lat": lat + dlat, "lng": lng + dlng}
            if is_crime:
                item["severity"] = 1
            data.append(item)
    return data

def _generate_businesses():
    data = []
    for b in BUSINESSES:
        data.append({"lat": b[0], "lng": b[1], "open_late": b[4], "closing_hour": b[5]})
    return data

def _generate_points(points):
    data = []
    for p in points:
        data.append({"lat": p[0], "lng": p[1]})
    return data

if __name__ == "__main__":
    print("Loading pedestrian Map Data for offline use...")
    base_graph = get_graph(vehicle_type="walk")
    
    print("Generating in-memory spatial layers for City-Wide Graph...")
    random.seed(42)
    sl = _generate_layer(STREETLIGHT_CLUSTERS, 3)
    cr = _generate_layer(CRIME_CLUSTERS, 3, is_crime=True)
    bz = _generate_businesses()
    sh = _generate_points(SAFE_HAVENS)
    th = _generate_points(TRANSIT_HUBS)
    cc = _generate_points(CCTV_ZONES)
    sp = _generate_points(SECURITY_POINTS)

    print("Applying 12-factor safety algorithms offline for the ENTIRE CITY...")
    weighted_graph = apply_safety_weights(
        base_graph,
        streetlights=sl, crimes=cr, businesses=bz, danger_pins=[],
        safe_havens=sh, cctv_zones=cc, transit_hubs=th, security_points=sp,
        start_lat=JAIPUR_BBOX["south"], start_lng=JAIPUR_BBOX["west"],
        end_lat=JAIPUR_BBOX["north"], end_lng=JAIPUR_BBOX["east"]
    )
    
    output_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "offline_graph.json"
    export_graph_to_json(weighted_graph, str(output_path))
