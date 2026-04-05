"""
Graph Builder — Downloads and caches the Jaipur road network.
Uses OSMnx to pull OpenStreetMap data and NetworkX for graph operations.
Enriches edges with road_type and safety attributes for the 12-factor scorer.

OPTIMIZED: Uses scipy cKDTree for O(E × log(D)) spatial queries instead of
           brute-force O(E × D) haversine distance calculations.
"""
import os
import logging
import pickle
import math
from datetime import datetime
from typing import Optional, List, Dict

import numpy as np
from scipy.spatial import cKDTree
import osmnx as ox
import networkx as nx

from graph.safety_scorer import calculate_edge_weight

logger = logging.getLogger("safeway")

# Core Jaipur bounding box (tightened to fit in 512MB RAM on free tiers)
JAIPUR_BBOX = {
    "north": 27.0100,
    "south": 26.8100,
    "east": 75.8900,
    "west": 75.6900,
}

# Approximate conversion at Jaipur's latitude (~26.9°N)
# 1 degree lat ≈ 111,320 meters
# 1 degree lng ≈ 111,320 * cos(26.9°) ≈ 99,280 meters
DEG_TO_M_LAT = 111_320.0
DEG_TO_M_LNG = 99_280.0


def _get_cache_path(vehicle_type: str) -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data", f"jaipur_graph_{vehicle_type}.pkl")

_graphs: Dict[str, nx.MultiDiGraph] = {}


def _is_night() -> bool:
    """Return True if current local time is between 6PM and 6AM."""
    hour = datetime.now().hour
    return hour >= 18 or hour < 6


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Calculate straight-line distance in meters between two lat/lng points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _extract_road_type(edge_data: dict) -> str:
    """Extract the highway classification tag from an OSM edge."""
    highway = edge_data.get("highway", "unclassified")
    if isinstance(highway, list):
        priority = ["primary", "secondary", "tertiary", "residential", "service", "footway", "path"]
        for p in priority:
            if p in highway:
                return p
        return highway[0]
    return highway


def _build_kdtree(data_list: list, bbox=None):
    """
    Build a cKDTree from a list of dicts with 'lat'/'lng' keys.
    Coordinates are converted to approximate meters for radius queries.
    Optionally filters to a bounding box first.
    Returns (tree, filtered_data, coords_meters) or (None, [], None) if empty.
    """
    if not data_list:
        return None, [], None

    if bbox:
        min_lat, max_lat, min_lng, max_lng = bbox
        data_list = [
            d for d in data_list
            if min_lat <= d["lat"] <= max_lat and min_lng <= d["lng"] <= max_lng
        ]

    if not data_list:
        return None, [], None

    coords = np.array([[d["lat"] * DEG_TO_M_LAT, d["lng"] * DEG_TO_M_LNG] for d in data_list])
    tree = cKDTree(coords)
    return tree, data_list, coords


def build_graph_from_osm(vehicle_type: str = "walk") -> nx.MultiDiGraph:
    """
    Download Jaipur road network from OpenStreetMap via OSMnx.
    Enriches every edge with road_type and zero-initialized safety attributes.
    """
    logger.info(f"📡 Downloading Jaipur {vehicle_type} network from OpenStreetMap...")
    logger.info("   (This may take 60-90 seconds on first run)")

    G = ox.graph_from_bbox(
        bbox=(
            JAIPUR_BBOX["north"],
            JAIPUR_BBOX["south"],
            JAIPUR_BBOX["east"],
            JAIPUR_BBOX["west"],
        ),
        network_type=vehicle_type,
        simplify=True,
    )

    G = ox.distance.add_edge_lengths(G)

    for u, v, k, data in G.edges(data=True, keys=True):
        length = data.get("length", 10.0)
        road_type = _extract_road_type(data)

        G[u][v][k]["custom_weight"] = length
        G[u][v][k]["road_type"] = road_type

        # Zero-initialize all safety counters
        G[u][v][k]["streetlight_count"] = 0
        G[u][v][k]["crime_count"] = 0
        G[u][v][k]["danger_pin_count"] = 0
        G[u][v][k]["safe_haven_count"] = 0
        G[u][v][k]["cctv_count"] = 0
        G[u][v][k]["transit_hub_count"] = 0
        G[u][v][k]["security_count"] = 0
        G[u][v][k]["business_count"] = 0

    logger.info(f"✅ Jaipur graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def save_graph(G: nx.MultiDiGraph, vehicle_type: str = "walk"):
    path = _get_cache_path(vehicle_type)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(G, f)
    logger.info(f"💾 Graph cached to {path}")


def load_graph(vehicle_type: str = "walk") -> Optional[nx.MultiDiGraph]:
    path = _get_cache_path(vehicle_type)
    if os.path.exists(path):
        logger.info(f"📂 Loading cached Jaipur {vehicle_type} graph...")
        with open(path, "rb") as f:
            G = pickle.load(f)
        
        # Convert to undirected graph once upon load to ensure A* pathfinding
        # is just as fast as walk mode, ignoring strict one-way constraints
        if vehicle_type in ["bike", "drive"]:
            G = G.to_undirected()
            
        logger.info(f"✅ Cached {vehicle_type} graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    return None


def get_graph(vehicle_type: str = "walk") -> nx.MultiDiGraph:
    """Return the graph, loading from cache or building from OSM."""
    global _graphs
    if vehicle_type in _graphs:
        return _graphs[vehicle_type]

    G = load_graph(vehicle_type)
    if G is None:
        G = build_graph_from_osm(vehicle_type)
        save_graph(G, vehicle_type)

    _graphs[vehicle_type] = G
    return G


def apply_safety_weights(
    G: nx.MultiDiGraph,
    streetlights: list,
    crimes: list,
    businesses: list,
    danger_pins: list,
    safe_havens: list = None,
    cctv_zones: list = None,
    transit_hubs: list = None,
    security_points: list = None,
    start_lat: float = None,
    start_lng: float = None,
    end_lat: float = None,
    end_lng: float = None,
) -> nx.MultiDiGraph:
    """
    Apply the 12-factor safety-weighted edge costs using spatial data.
    
    OPTIMIZED: Uses cKDTree spatial indexing instead of brute-force haversine.
    This reduces complexity from O(E × D) to O(E × log(D)).
    """
    import time
    t0 = time.perf_counter()

    safe_havens = safe_havens or []
    cctv_zones = cctv_zones or []
    transit_hubs = transit_hubs or []
    security_points = security_points or []

    # Bounding box of the journey plus 2km padding (~0.02 degrees)
    min_lat = min(start_lat, end_lat) - 0.02
    max_lat = max(start_lat, end_lat) + 0.02
    min_lng = min(start_lng, end_lng) - 0.02
    max_lng = max(start_lng, end_lng) + 0.02
    bbox = (min_lat, max_lat, min_lng, max_lng)

    # Build KD-trees for each data layer (pre-filtered to route bbox + extra padding)
    # Padding the data bbox slightly larger than route bbox so radius queries at edges work
    data_bbox = (min_lat - 0.005, max_lat + 0.005, min_lng - 0.005, max_lng + 0.005)

    tree_sl, sl_data, _ = _build_kdtree(streetlights, data_bbox)
    tree_cr, cr_data, _ = _build_kdtree(crimes, data_bbox)
    tree_dp, dp_data, _ = _build_kdtree(danger_pins, data_bbox)
    tree_sh, sh_data, _ = _build_kdtree(safe_havens, data_bbox)
    tree_cc, cc_data, _ = _build_kdtree(cctv_zones, data_bbox)
    tree_th, th_data, _ = _build_kdtree(transit_hubs, data_bbox)
    tree_sp, sp_data, _ = _build_kdtree(security_points, data_bbox)
    tree_bz, bz_data, _ = _build_kdtree(businesses, data_bbox)

    # Radii in meters for each data layer
    R_STREETLIGHT = 10.0
    R_CRIME = 50.0
    R_DANGER_PIN = 20.0
    R_SAFE_HAVEN = 100.0
    R_CCTV = 50.0
    R_TRANSIT = 80.0
    R_SECURITY = 40.0
    R_BUSINESS = 30.0

    edges_processed = 0

    for u, v, k, data in G.edges(data=True, keys=True):
        node_u = G.nodes[u]
        node_v = G.nodes[v]
        mid_lat = (node_u["y"] + node_v["y"]) / 2
        mid_lng = (node_u["x"] + node_v["x"]) / 2

        # Skip edges outside route bounding box
        if not (min_lat <= mid_lat <= max_lat and min_lng <= mid_lng <= max_lng):
            continue

        edges_processed += 1

        # Convert edge midpoint to meters for KD-tree queries
        mid_m = np.array([mid_lat * DEG_TO_M_LAT, mid_lng * DEG_TO_M_LNG])

        # Query each KD-tree for counts within radius
        s_count = len(tree_sl.query_ball_point(mid_m, R_STREETLIGHT)) if tree_sl else 0
        c_count = len(tree_cr.query_ball_point(mid_m, R_CRIME)) if tree_cr else 0
        d_count = len(tree_dp.query_ball_point(mid_m, R_DANGER_PIN)) if tree_dp else 0
        h_count = len(tree_sh.query_ball_point(mid_m, R_SAFE_HAVEN)) if tree_sh else 0
        cc_count = len(tree_cc.query_ball_point(mid_m, R_CCTV)) if tree_cc else 0
        t_count = len(tree_th.query_ball_point(mid_m, R_TRANSIT)) if tree_th else 0
        sec_count = len(tree_sp.query_ball_point(mid_m, R_SECURITY)) if tree_sp else 0

        # Businesses within radius — need full entries for closing_hour
        if tree_bz:
            biz_indices = tree_bz.query_ball_point(mid_m, R_BUSINESS)
            nearby_biz = [bz_data[i] for i in biz_indices]
        else:
            nearby_biz = []

        road_type = data.get("road_type", "unclassified")
        length = data.get("length", 10.0)

        weight = calculate_edge_weight(
            length_m=length,
            streetlight_count=s_count,
            crime_count=c_count,
            danger_pin_count=d_count,
            road_type=road_type,
            safe_haven_count=h_count,
            cctv_count=cc_count,
            transit_hub_count=t_count,
            security_count=sec_count,
            business_entries=nearby_biz,
        )

        G[u][v][k]["custom_weight"] = weight
        G[u][v][k]["streetlight_count"] = s_count
        G[u][v][k]["crime_count"] = c_count
        G[u][v][k]["danger_pin_count"] = d_count
        G[u][v][k]["safe_haven_count"] = h_count
        G[u][v][k]["cctv_count"] = cc_count
        G[u][v][k]["transit_hub_count"] = t_count
        G[u][v][k]["security_count"] = sec_count
        G[u][v][k]["business_count"] = len(nearby_biz)

    elapsed = time.perf_counter() - t0
    logger.info(f"⚡ Safety weights applied to {edges_processed} edges in {elapsed:.2f}s (KD-tree optimized)")

    return G
