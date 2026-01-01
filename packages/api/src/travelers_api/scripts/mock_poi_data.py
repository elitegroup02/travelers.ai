"""Mock POI data for simulation.

Provides runtime enrichment for POI fields not stored in the database.
This allows the simulation to generate varied, realistic scenarios
without requiring database schema changes.
"""

import hashlib
import random
from typing import Any


# Price ranges by POI type (in EUR)
POI_PRICE_RANGES: dict[str, tuple[float, float]] = {
    "museum": (12, 28),
    "monument": (14, 22),
    "church": (0, 10),  # Many churches are free or donation-based
    "park": (0, 8),  # Usually free, some have paid sections
    "theater": (25, 150),
    "building": (10, 22),
    "government": (0, 18),  # Many offer free tours
}

# Opening hours templates with realistic variations
OPENING_HOURS_TEMPLATES: dict[str, str] = {
    "standard": "9:00-17:00",
    "extended": "8:00-20:00",
    "late_opening": "10:00-22:00",
    "early_bird": "6:00-14:00",
    "afternoon": "12:00-20:00",
    "closed_monday": "Tue-Sun 9:00-18:00",
    "closed_tuesday": "Mon, Wed-Sun 10:00-17:00",
    "seasonal_summer": "Apr-Oct: 9:00-19:00, Nov-Mar: 10:00-16:00",
    "seasonal_winter": "Nov-Feb: 10:00-16:00, Mar-Oct: 9:00-18:00",
    "limited_weekend": "Weekdays 9:00-17:00, Weekends 10:00-15:00",
    "extended_weekend": "Mon-Fri 9:00-17:00, Sat-Sun 9:00-20:00",
}

# Major landmarks that typically have higher prices and longer waits
MAJOR_LANDMARKS = [
    "colosseum",
    "vatican",
    "eiffel",
    "statue of liberty",
    "pyramids",
    "sagrada familia",
    "tower of london",
    "louvre",
    "uffizi",
    "british museum",
    "metropolitan",
    "notre-dame",
    "taj mahal",
    "machu picchu",
    "petra",
    "acropolis",
]

# Crowd level factors by city (base multiplier)
CITY_CROWD_FACTORS: dict[str, float] = {
    "Rome": 1.3,
    "Paris": 1.4,
    "Barcelona": 1.2,
    "London": 1.3,
    "New York": 1.2,
    "Tokyo": 1.1,
    "Cairo": 0.9,
    "Sydney": 0.8,
    "Marrakech": 0.85,
    "Buenos Aires": 0.75,
}

# Best times based on POI type
BEST_TIMES_BY_TYPE: dict[str, list[str]] = {
    "museum": ["morning", "late_afternoon", "weekday"],
    "monument": ["early_morning", "sunset", "weekday"],
    "church": ["morning", "weekday", "during_mass"],
    "park": ["morning", "late_afternoon", "anytime"],
    "theater": ["evening", "matinee"],
    "building": ["morning", "afternoon"],
    "government": ["morning", "weekday"],
}

# Accessibility levels
ACCESSIBILITY_OPTIONS = ["full", "partial", "limited", "stairs_only", "elevator_available"]


def _get_seed(poi_name: str, city_name: str) -> int:
    """Generate a consistent seed for a POI so mock data is reproducible."""
    combined = f"{poi_name.lower()}:{city_name.lower()}"
    return int(hashlib.md5(combined.encode()).hexdigest()[:8], 16)


def get_mock_poi_data(
    poi_name: str,
    poi_type: str | None,
    city_name: str,
    *,
    randomize: bool = False,
) -> dict[str, Any]:
    """Generate mock data for a POI based on its type and location.

    Args:
        poi_name: Name of the POI
        poi_type: Type of POI (museum, monument, church, etc.)
        city_name: Name of the city
        randomize: If True, adds some randomness. If False, same POI always gets same data.

    Returns:
        Dictionary with mock fields:
        - poi_price_eur: Entry price
        - poi_price_skip_line_eur: Skip-the-line ticket price (if applicable)
        - poi_opening_hours: Opening hours string
        - poi_rating: Visitor rating (1-5)
        - poi_review_count: Number of reviews
        - poi_crowd_level: Expected crowd level
        - poi_accessibility: Accessibility information
        - poi_best_time: Best time to visit
        - poi_typical_duration_mins: Typical visit duration
        - poi_booking_required: Whether advance booking is recommended
    """
    # Use consistent seed unless randomizing
    if not randomize:
        seed = _get_seed(poi_name, city_name)
        rng = random.Random(seed)
    else:
        rng = random.Random()

    poi_type = poi_type or "monument"
    price_range = POI_PRICE_RANGES.get(poi_type, (8, 20))

    # Check if this is a major landmark
    is_major = any(landmark in poi_name.lower() for landmark in MAJOR_LANDMARKS)

    # Base price calculation
    base_price = rng.uniform(*price_range)
    if is_major:
        base_price *= 1.4  # Major landmarks cost more

    # Some POIs are free
    is_free = base_price < 3 or (poi_type in ["church", "park"] and rng.random() < 0.4)
    final_price = 0.0 if is_free else round(base_price, 2)

    # Skip-the-line price (only for paid attractions with crowds)
    skip_line_price = None
    if final_price > 0 and is_major:
        skip_line_price = round(final_price * rng.uniform(1.5, 2.0), 2)

    # Opening hours - major attractions often have extended hours
    if is_major:
        hours_options = ["extended", "seasonal_summer", "extended_weekend"]
    elif poi_type == "church":
        hours_options = ["standard", "early_bird", "limited_weekend"]
    else:
        hours_options = list(OPENING_HOURS_TEMPLATES.keys())
    opening_hours = OPENING_HOURS_TEMPLATES[rng.choice(hours_options)]

    # Rating - major landmarks and museums tend to rate higher
    if is_major:
        rating = round(rng.uniform(4.3, 4.9), 1)
    elif poi_type == "museum":
        rating = round(rng.uniform(4.0, 4.8), 1)
    else:
        rating = round(rng.uniform(3.8, 4.7), 1)

    # Review count scales with fame
    if is_major:
        review_count = rng.randint(15000, 80000)
    else:
        review_count = rng.randint(500, 15000)

    # Crowd level based on city and POI type
    city_factor = CITY_CROWD_FACTORS.get(city_name, 1.0)
    crowd_score = rng.uniform(0.3, 1.0) * city_factor
    if is_major:
        crowd_score *= 1.3
    crowd_score = min(crowd_score, 1.0)

    if crowd_score > 0.8:
        crowd_level = "very_high"
    elif crowd_score > 0.6:
        crowd_level = "high"
    elif crowd_score > 0.4:
        crowd_level = "moderate"
    else:
        crowd_level = "low"

    # Accessibility
    if poi_type in ["park", "monument"]:
        accessibility = rng.choice(["full", "partial", "full"])
    elif poi_type == "church":
        accessibility = rng.choice(["partial", "limited", "stairs_only"])
    else:
        accessibility = rng.choice(ACCESSIBILITY_OPTIONS)

    # Best time to visit
    best_times = BEST_TIMES_BY_TYPE.get(poi_type, ["morning", "afternoon"])
    best_time = rng.choice(best_times)

    # Booking required for major attractions
    booking_required = is_major or (final_price > 15 and rng.random() < 0.6)

    return {
        "poi_price_eur": final_price,
        "poi_price_skip_line_eur": skip_line_price,
        "poi_opening_hours": opening_hours,
        "poi_rating": rating,
        "poi_review_count": review_count,
        "poi_crowd_level": crowd_level,
        "poi_accessibility": accessibility,
        "poi_best_time": best_time,
        "poi_booking_required": booking_required,
        "poi_is_major_landmark": is_major,
    }


def get_simulated_current_time_context(
    poi_opening_hours: str,
    *,
    simulate_hour: int | None = None,
) -> dict[str, Any]:
    """Generate time-related context for warnings and tips.

    Args:
        poi_opening_hours: Opening hours string from get_mock_poi_data
        simulate_hour: Hour of day to simulate (0-23). If None, uses random realistic hour.

    Returns:
        Dictionary with:
        - current_hour: Simulated current hour
        - closing_soon: Whether attraction closes within 2 hours
        - time_until_close_mins: Minutes until closing (if applicable)
        - is_open: Whether currently open
    """
    rng = random.Random()

    # Default to realistic tourist hours (8am - 8pm)
    if simulate_hour is None:
        simulate_hour = rng.randint(8, 20)

    # Parse simple opening hours (handles "9:00-17:00" format)
    try:
        if "-" in poi_opening_hours and ":" in poi_opening_hours:
            parts = poi_opening_hours.split("-")
            if len(parts) >= 2:
                close_time = parts[1].strip().split()[0]  # Handle "17:00" or "17:00,"
                close_hour = int(close_time.split(":")[0])
            else:
                close_hour = 18
        else:
            close_hour = 18  # Default
    except (ValueError, IndexError):
        close_hour = 18

    time_until_close = (close_hour - simulate_hour) * 60
    is_open = 8 <= simulate_hour < close_hour
    closing_soon = is_open and time_until_close <= 120

    return {
        "current_hour": simulate_hour,
        "closing_soon": closing_soon,
        "time_until_close_mins": max(0, time_until_close) if is_open else 0,
        "is_open": is_open,
    }


def get_warning_triggers(
    mock_data: dict[str, Any],
    time_context: dict[str, Any],
    budget_remaining: float | None = None,
    party_size: int = 1,
) -> list[dict[str, str]]:
    """Generate warning triggers based on context for WarningLens.

    Returns list of warnings that could be surfaced, each with:
    - type: Warning category
    - message: Short warning message
    - priority: "high", "medium", or "low"
    """
    warnings = []

    # Time-based warnings
    if time_context.get("closing_soon"):
        mins = time_context.get("time_until_close_mins", 0)
        warnings.append({
            "type": "time_constraint",
            "message": f"Closes in {mins} minutes - may not have enough time",
            "priority": "high" if mins < 60 else "medium",
        })

    if not time_context.get("is_open"):
        warnings.append({
            "type": "closed",
            "message": "Currently closed",
            "priority": "high",
        })

    # Crowd warnings
    if mock_data.get("poi_crowd_level") == "very_high":
        warnings.append({
            "type": "crowds",
            "message": "Expect very long queues - consider skip-the-line tickets",
            "priority": "medium",
        })

    # Budget warnings
    if budget_remaining is not None:
        total_cost = (mock_data.get("poi_price_eur") or 0) * party_size
        if total_cost > budget_remaining:
            warnings.append({
                "type": "budget",
                "message": f"Entry ({total_cost:.0f}) exceeds remaining budget ({budget_remaining:.0f})",
                "priority": "high",
            })
        elif total_cost > budget_remaining * 0.5:
            warnings.append({
                "type": "budget",
                "message": f"Entry will use {total_cost/budget_remaining*100:.0f}% of remaining budget",
                "priority": "medium",
            })

    # Booking warnings
    if mock_data.get("poi_booking_required"):
        warnings.append({
            "type": "booking",
            "message": "Advance booking recommended - may sell out",
            "priority": "medium",
        })

    # Accessibility warnings (if mobility constraints would be relevant)
    if mock_data.get("poi_accessibility") in ["limited", "stairs_only"]:
        warnings.append({
            "type": "accessibility",
            "message": f"Limited accessibility: {mock_data.get('poi_accessibility')}",
            "priority": "low",
        })

    return warnings
