"""
Pre-build the Jaipur road graphs during Render's BUILD phase.

Render's build environment has 2GB+ RAM, but the runtime (free tier)
only has 512MB. OSMnx graph download needs ~800MB, so we do it here
and pickle the result for the runtime to load cheaply.

Builds all 3 travel modes: walk, bike, drive.
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("safeway")

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graph.builder import get_graph

if __name__ == "__main__":
    logger.info("🏗️  Pre-building Jaipur road graphs during BUILD phase...")
    logger.info("   (This uses Render's build RAM, not the 512MB runtime)")

    for mode in ["walk", "bike", "drive"]:
        logger.info(f"── Building {mode} graph ──")
        G = get_graph(mode)
        logger.info(f"✅ {mode} graph cached: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    logger.info("🎉 All 3 graphs pre-built and cached to disk.")
    logger.info("   The runtime will load these pickles instantly without OSMnx.")
