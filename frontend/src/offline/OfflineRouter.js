import createGraph from 'ngraph.graph';
import { aStar } from 'ngraph.path';
import localforage from 'localforage';

class OfflineRouterEngine {
  constructor() {
    this.graph = createGraph();
    this.nodesMap = new Map();
    this.isLoaded = false;
    this.loadingPromise = null;
    this.pathfinder = null;
  }

  async initialize() {
    if (this.isLoaded) return true;
    if (this.loadingPromise) return this.loadingPromise;

    this.loadingPromise = this._loadGraphData();
    return this.loadingPromise;
  }

  async _loadGraphData() {
    try {
      console.log('[OfflineRouter] Checking local cache for Jaipur offline graph...');
      let graphData = await localforage.getItem('jaipur_offline_graph_v1');

      if (!graphData) {
        console.log('[OfflineRouter] Graph not in cache. Downloading (48MB)...');
        const res = await fetch('/offline_graph.json');
        if (!res.ok) throw new Error('Offline graph download failed');
        graphData = await res.json();
        
        console.log('[OfflineRouter] Caching to IndexedDB via localforage...');
        await localforage.setItem('jaipur_offline_graph_v1', graphData);
      } else {
        console.log('[OfflineRouter] Loaded graph from offline cache!');
      }

      console.log(`[OfflineRouter] Building ngraph instance (${graphData.nodes.length} nodes)...`);
      
      // Add nodes
      for (const node of graphData.nodes) {
        this.graph.addNode(node.id, node.data);
        this.nodesMap.set(node.id, node.data);
      }

      // Add edges
      for (const link of graphData.links) {
        this.graph.addLink(link.fromId, link.toId, link.data);
      }

      // Initialize A* with our custom safety weight (which was pre-calculated offline)
      // and Haversine heuristic.
      this.pathfinder = aStar(this.graph, {
        distance(fromNode, toNode, link) {
          return link.data.weight; // The safety-weighted cost
        },
        heuristic(fromNode, toNode) {
          // Haversine distance heuristic (straight line)
          const lat1 = fromNode.data.lat, lon1 = fromNode.data.lng;
          const lat2 = toNode.data.lat, lon2 = toNode.data.lng;
          const R = 6371e3; // meters
          const phi1 = lat1 * Math.PI/180;
          const phi2 = lat2 * Math.PI/180;
          const dphi = (lat2-lat1) * Math.PI/180;
          const dlambda = (lon2-lon1) * Math.PI/180;
          const a = Math.sin(dphi/2) * Math.sin(dphi/2) +
                    Math.cos(phi1) * Math.cos(phi2) *
                    Math.sin(dlambda/2) * Math.sin(dlambda/2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
          return R * c;
        }
      });

      this.isLoaded = true;
      console.log('[OfflineRouter] Ready for offline routing!');
      return true;
    } catch (e) {
      console.error('[OfflineRouter] Initialization failed:', e);
      return false;
    }
  }

  // Find nearest node simply by checking bounding box then minimum distance
  _findNearestNode(lat, lng) {
    let bestDist = Infinity;
    let bestNode = null;
    
    // O(N) search because KD-tree in JS is heavy to build for 130k nodes 
    // Optimization: could restrict bounding box search first.
    for (const [id, data] of this.nodesMap.entries()) {
      // Fast rough geographic bounds check (within ~3km)
      if (Math.abs(data.lat - lat) > 0.03 || Math.abs(data.lng - lng) > 0.03) continue;

      const R = 6371e3;
      const phi1 = lat * Math.PI/180, phi2 = data.lat * Math.PI/180;
      const dphi = (data.lat-lat) * Math.PI/180;
      const dlambda = (data.lng-lng) * Math.PI/180;
      const a = Math.sin(dphi/2) * Math.sin(dphi/2) +
                Math.cos(phi1) * Math.cos(phi2) *
                Math.sin(dlambda/2) * Math.sin(dlambda/2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      const d = R * c;

      if (d < bestDist) {
        bestDist = d;
        bestNode = id;
      }
    }
    return bestNode;
  }

  async calculateRoute(startCoords, endCoords) {
    if (!this.isLoaded) throw new Error("Offline Engine not initialized");

    const startNode = this._findNearestNode(startCoords[0], startCoords[1]);
    const endNode = this._findNearestNode(endCoords[0], endCoords[1]);

    if (!startNode || !endNode) {
      throw new Error("Points are outside of the offline cached map area.");
    }

    const path = this.pathfinder.find(startNode, endNode);
    if (!path || path.length === 0) {
      throw new Error("No offline path found.");
    }

    // Path from ngraph is returned End to Start. Reverse it.
    path.reverse();

    // Aggregate statistics
    const coordinates = [];
    let totalDist = 0;
    let litCount = 0;
    let shCount = 0;
    let totalWeight = 0;

    for (let i = 0; i < path.length; i++) {
        coordinates.push([path[i].data.lng, path[i].data.lat]);
        
        // Find link between path[i] and path[i+1]
        if (i < path.length - 1) {
            const link = this.graph.getLink(path[i].id, path[i+1].id) || this.graph.getLink(path[i+1].id, path[i].id);
            if (link) {
                totalDist += link.data.dist;
                litCount += link.data.lit;
                shCount += link.data.sh;
                totalWeight += link.data.weight;
            }
        }
    }

    // Mock safety score based on average weight comparison (similar to python logic)
    const avgWeight = totalWeight / (path.length || 1);
    const safetyScore = Math.max(30, Math.min(99, Math.round(100 - (avgWeight * 2))));

    // Return format matches FastAPI response
    return [{
        coordinates: coordinates,
        safety_score: safetyScore,
        distance_m: Math.round(totalDist),
        duration_min: Math.round(totalDist / 83.3 * 10) / 10,
        lit_segments: litCount,
        dark_segments: Math.max(0, path.length - litCount),
        safe_haven_count: shCount,
        transit_nearby: 0,
        cctv_segments: 0,
        street_names: ["Offline Route (Local Cache)"],
        is_offline: true // Flag to tell UI this was calculated physically on device
    }];
  }
}

// Singleton instance
export const offlineRouter = new OfflineRouterEngine();
