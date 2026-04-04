"""
A* Pathfinder — Finds the safest pedestrian routes between two points in Jaipur.
Uses NetworkX astar_path with custom 12-factor safety weights.
Extracts safe_haven_count, cctv_segments, transit_nearby, and road_quality from edges.
"""
import math
from typing import List, Dict, Any

import networkx as nx
import osmnx as ox

from graph.safety_scorer import weight_to_safety_score


def _haversine_heuristic(u, v, G: nx.MultiDiGraph) -> float:
    """
    A* heuristic: straight-line geographic distance between node u and goal v.
    """
    node_u = G.nodes[u]
    node_v = G.nodes[v]
    lat1, lon1 = node_u["y"], node_u["x"]
    lat2, lon2 = node_v["y"], node_v["x"]

    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Road quality classification for display
GOOD_ROADS = {"primary", "secondary", "tertiary", "trunk", "motorway", "pedestrian"}
MODERATE_ROADS = {"residential", "unclassified", "living_street", "cycleway"}
POOR_ROADS = {"service", "footway", "path", "track"}


def _classify_road_quality(road_types: list) -> str:
    """Classify overall route road quality from edge road types."""
    if not road_types:
        return "mixed"
    good = sum(1 for r in road_types if r in GOOD_ROADS)
    poor = sum(1 for r in road_types if r in POOR_ROADS)
    total = len(road_types)
    if good / total >= 0.6:
        return "well-paved"
    elif poor / total >= 0.4:
        return "narrow-alleys"
    return "mixed"


def calculate_safe_routes(
    G: nx.MultiDiGraph,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    k_routes: int = 3,
    vehicle_type: str = "walk"
) -> List[Dict[str, Any]]:
    """
    Calculate the top K safest pedestrian routes using a penalty-based A* method.
    Returns a list of routes sorted by safety score, with full 12-factor metrics.
    """
    # G is now passed in as a pre-filtered subgraph from routes.py

    start_node = ox.distance.nearest_nodes(G, X=start_lng, Y=start_lat)
    end_node = ox.distance.nearest_nodes(G, X=end_lng, Y=end_lat)

    if start_node == end_node:
        raise ValueError("Start and end points are too close together")

    routes = []
    changed_edges = {}

    for route_idx in range(k_routes):
        try:
            path_nodes = nx.astar_path(
                G,
                source=start_node,
                target=end_node,
                heuristic=lambda u, v: _haversine_heuristic(u, v, G),
                weight="custom_weight",
            )
        except nx.NetworkXNoPath:
            # Fallback for Cars/Bikes: the graph strict one-ways might block the start/end snapped nodes.
            # Convert to undirected temporarily just to ensure a path is mathematically found.
            try:
                path_nodes = nx.astar_path(
                    G.to_undirected(),
                    source=start_node,
                    target=end_node,
                    heuristic=lambda u, v: _haversine_heuristic(u, v, G),
                    weight="custom_weight",
                )
            except nx.NetworkXNoPath:
                break

        # Extract coordinates and stats from path
        coordinates = []
        total_weight = 0.0
        total_length = 0.0
        lit_segments = 0
        dark_segments = 0
        street_names = set()
        all_weights = []
        road_types = []

        # New 12-factor accumulators
        total_safe_havens = 0
        total_cctv = 0
        total_transit = 0

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            edge_data = G.get_edge_data(u, v)

            if edge_data:
                best_k = None
                best_weight = float('inf')

                for e_key in edge_data:
                    e_weight = edge_data[e_key].get("custom_weight", 10.0)
                    if e_weight < best_weight:
                        best_weight = e_weight
                        best_k = e_key

                    if (u, v, e_key) not in changed_edges:
                        changed_edges[(u, v, e_key)] = e_weight

                    G[u][v][e_key]["custom_weight"] = e_weight * 1.5

                best_edge = edge_data[best_k] if best_k is not None else min(
                    edge_data.values(), key=lambda e: e.get("custom_weight", float("inf"))
                )

                orig_weight = changed_edges.get((u, v, best_k), best_edge.get("custom_weight", 10.0))

                length = best_edge.get("length", 10.0)
                s_count = best_edge.get("streetlight_count", 0)
                name = best_edge.get("name", "")
                road_type = best_edge.get("road_type", "unclassified")

                total_weight += orig_weight
                total_length += length
                all_weights.append(orig_weight)
                road_types.append(road_type)

                if s_count > 0:
                    lit_segments += 1
                else:
                    dark_segments += 1

                # Accumulate new metrics
                total_safe_havens += best_edge.get("safe_haven_count", 0)
                total_cctv += 1 if best_edge.get("cctv_count", 0) > 0 else 0
                total_transit += best_edge.get("transit_hub_count", 0)

                if name:
                    if isinstance(name, list):
                        street_names.update(name)
                    else:
                        street_names.add(name)

            node = G.nodes[path_nodes[i]]
            coordinates.append([node["x"], node["y"]])

        # Add last node
        last_node = G.nodes[path_nodes[-1]]
        coordinates.append([last_node["x"], last_node["y"]])

        if all_weights:
            avg_weight = total_weight / len(all_weights)
            min_w = min(all_weights)
            max_w = max(all_weights)
            safety_score = weight_to_safety_score(avg_weight, min_w, max_w)
        else:
            safety_score = 50

        duration_min = round(total_length / 83.3, 1)

        routes.append({
            "coordinates": coordinates,
            "safety_score": safety_score,
            "distance_m": round(total_length),
            "duration_min": duration_min,
            "lit_segments": lit_segments,
            "dark_segments": dark_segments,
            "street_names": list(street_names)[:5],
            "node_count": len(path_nodes),
            "route_index": route_idx,
            # New 12-factor fields
            "safe_haven_count": total_safe_havens,
            "cctv_segments": total_cctv,
            "transit_nearby": total_transit,
            "road_quality": _classify_road_quality(road_types),
        })

    # Restore ALL original edge weights before returning
    for (u, v, key), old_w in changed_edges.items():
        G[u][v][key]["custom_weight"] = old_w

    if not routes:
        raise ValueError("No walkable route found between these points")

    routes.sort(key=lambda r: r["safety_score"], reverse=True)
    return routes
