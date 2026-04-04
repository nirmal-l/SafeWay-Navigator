"""
Safety Scorer — Advanced 12-Factor Weighted Safety Engine for Jaipur.

Calculates custom edge weights for the road graph using:
  Tier 1: Infrastructure & Urban Design (road type, safe havens, CCTV, lights)
  Tier 2: Dynamic & Temporal (time-decay, dark night, peak danger window)
  Tier 3: Micro-Level & Community (crime, danger pins, transit, security)

See implementation_plan.md for the full factor table.
"""
from datetime import datetime

# ── Tier 1: Infrastructure & Urban Design ─────────────────────────────────────
STREETLIGHT_BONUS = 0.5         # Per streetlight within 10m — reduces weight
SAFE_HAVEN_BONUS = 4.0          # Per police/hospital/fire station within 100m
CCTV_BONUS = 3.0                # Per CCTV camera within 50m
ROAD_HIERARCHY = {               # Bonus/penalty based on OSM highway tag
    "motorway": -4.0,
    "trunk": -3.5,
    "primary": -3.0,
    "secondary": -2.0,
    "tertiary": -1.0,
    "unclassified": 0.0,
    "residential": 6.0,          # Narrow residential → penalty
    "service": 8.0,              # Back alleys → strong penalty
    "footway": 5.0,              # Footpaths can be isolated at night
    "path": 10.0,                # Unpaved/dirt → avoid at night
    "track": 12.0,               # Rural track → strongly avoid
    "living_street": 3.0,
    "pedestrian": -1.0,          # Pedestrian zones are usually safe
    "cycleway": 4.0,
}
DEFAULT_ROAD_PENALTY = 2.0       # For unknown road types

# ── Tier 2: Dynamic & Temporal ────────────────────────────────────────────────
BUSINESS_BONUS_FULL = 1.5        # Per open business within 30m (during hours)
BUSINESS_BONUS_CLOSING = 0.75    # Reduced bonus within 1hr of closing
DARK_NIGHT_PENALTY = 25.0        # If nighttime AND zero streetlights
PEAK_DANGER_MULTIPLIER = 1.3     # Applied 10PM–2AM on all penalties

# ── Tier 3: Micro-Level & Community ───────────────────────────────────────────
CRIME_PENALTY = 5.0              # Per crime within 50m
DANGER_PIN_PENALTY = 10.0        # Per community pin within 20m
TRANSIT_HUB_BONUS = 2.0          # Per transit hub within 80m
SECURITY_POINT_BONUS = 1.5       # Per ATM/hotel/gated society within 40m

# ── Global ────────────────────────────────────────────────────────────────────
MIN_EDGE_WEIGHT = 1.0            # Floor — prevents negative/zero weights


def _get_time_context() -> dict:
    """Return current time context for dynamic scoring."""
    now = datetime.now()
    hour = now.hour
    return {
        "hour": hour,
        "is_night": hour >= 18 or hour < 6,
        "is_peak_danger": hour >= 22 or hour < 2,
    }


def _business_time_decay(business_closing_hour: int, current_hour: int) -> float:
    """
    Calculate time-decay multiplier for a business.
    Returns: 1.0 (fully open), 0.5 (within 1hr of closing), 0.0 (closed).
    """
    if business_closing_hour == 0:  # 24/7 business
        return 1.0

    # Hours since closing (handle midnight wrap)
    hours_since_close = (current_hour - business_closing_hour) % 24
    if hours_since_close > 12:
        # Business hasn't closed yet (we're before closing time)
        return 1.0
    elif hours_since_close == 0:
        return 0.5  # Just closed
    elif hours_since_close == 1:
        return 0.25
    else:
        return 0.0  # Closed > 1 hour ago


def calculate_edge_weight(
    length_m: float,
    streetlight_count: int,
    crime_count: int,
    danger_pin_count: int,
    road_type: str,
    safe_haven_count: int = 0,
    cctv_count: int = 0,
    transit_hub_count: int = 0,
    security_count: int = 0,
    business_entries: list = None,
) -> float:
    """
    Calculate the safety-adjusted edge weight for a road segment.
    Higher weight = less safe = A* avoids it.
    Lower weight = safer = A* prefers it.

    Args:
        length_m: Physical length (meters)
        streetlight_count: Streetlights within 10m
        crime_count: Crime incidents within 50m
        danger_pin_count: Active community pins within 20m
        road_type: OSM highway classification tag
        safe_haven_count: Police/hospital/fire within 100m
        cctv_count: CCTV cameras within 50m
        transit_hub_count: Bus/auto/metro within 80m
        security_count: ATMs/hotels within 40m
        business_entries: List of dicts with 'closing_hour' keys for time-decay

    Returns:
        Float safety weight (higher = more dangerous)
    """
    time_ctx = _get_time_context()
    weight = length_m

    # ── Tier 1: Infrastructure ────────────────────────────────────────────
    weight -= streetlight_count * STREETLIGHT_BONUS
    weight -= safe_haven_count * SAFE_HAVEN_BONUS
    weight -= cctv_count * CCTV_BONUS
    weight += ROAD_HIERARCHY.get(road_type, DEFAULT_ROAD_PENALTY)

    # ── Tier 2: Dynamic / Temporal ────────────────────────────────────────
    if business_entries:
        for biz in business_entries:
            closing_hr = biz.get("closing_hour", 0)
            decay = _business_time_decay(closing_hr, time_ctx["hour"])
            weight -= decay * BUSINESS_BONUS_FULL
    
    if time_ctx["is_night"] and streetlight_count == 0:
        weight += DARK_NIGHT_PENALTY

    # ── Tier 3: Micro-Level / Community ───────────────────────────────────
    weight += crime_count * CRIME_PENALTY
    weight += danger_pin_count * DANGER_PIN_PENALTY
    weight -= transit_hub_count * TRANSIT_HUB_BONUS
    weight -= security_count * SECURITY_POINT_BONUS

    # ── Peak Danger Window Multiplier (10PM–2AM) ──────────────────────────
    if time_ctx["is_peak_danger"]:
        # Only amplify the penalty portion (weight above base length)
        penalty_portion = max(0, weight - length_m)
        bonus_portion = min(0, weight - length_m)
        weight = length_m + (penalty_portion * PEAK_DANGER_MULTIPLIER) + bonus_portion

    return max(weight, MIN_EDGE_WEIGHT)


def weight_to_safety_score(weight: float, min_w: float, max_w: float) -> int:
    """
    Convert a raw edge weight to a 0-100 safety score for display.
    100 = perfectly safe, 0 = avoid at all costs.
    """
    if max_w == min_w:
        return 100
    normalized = (weight - min_w) / (max_w - min_w)
    return max(0, min(100, int(100 * (1 - normalized))))
