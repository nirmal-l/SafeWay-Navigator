"""
Pre-build the Jaipur road graph during Render's BUILD phase.

Render's build environment has 2GB+ RAM, but the runtime (free tier)
only has 512MB. OSMnx graph download needs ~800MB, so we do it here
and pickle the result for the runtime to load cheaply.
"""
import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph.builder import get_graph

if __name__ == "__main__":
    print("🏗️  Pre-building Jaipur walk graph during BUILD phase...")
    print("   (This uses Render's build RAM, not the 512MB runtime)")
    G = get_graph("walk")
    print(f"✅ Graph cached to disk: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print("   The runtime will load this pickle instantly without OSMnx.")
