"""Omen Dashboard Activity Simulator - Enhanced Version.

Generates realistic user activity for thoroughly testing Omen's connection,
streaming, and response quality with:
- User personas (budget, family, luxury, cultural, senior travelers)
- Realistic timing patterns (15-90s reads, 0.5-2s navigation)
- Rich metadata for all Omen lens types
- Narrative journey arcs instead of random transitions
- Context-aware chat questions
- Conversation history tracking

Usage:
    # Default 3-minute simulation with random persona
    python -m travelers_api.scripts.simulate_activity

    # Specific persona
    python -m travelers_api.scripts.simulate_activity --persona family_vacation

    # Quick test mode (faster timing)
    python -m travelers_api.scripts.simulate_activity --quick-mode --duration 60

    # Verbose logging
    python -m travelers_api.scripts.simulate_activity --verbose
"""

import argparse
import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import select

from travelers_api.clients.omen import OmenClient, OmenScreen
from travelers_api.core.database import async_session_maker
from travelers_api.models.city import City
from travelers_api.models.poi import POI
from travelers_api.scripts.mock_poi_data import (
    get_mock_poi_data,
    get_simulated_current_time_context,
    get_warning_triggers,
)

logger = logging.getLogger(__name__)


# =============================================================================
# User Persona System
# =============================================================================


@dataclass
class UserPersona:
    """Represents a simulated user type with preferences and constraints."""

    name: str
    persona_type: str  # "budget", "family", "luxury", "cultural", "senior"

    # Trip characteristics
    trip_duration_days: int
    daily_budget_eur: float
    party_size: int
    has_children: bool
    mobility_constraints: bool

    # Trip dates (set dynamically)
    trip_start_date: date = field(default_factory=lambda: date.today())

    # Preferences
    preferred_poi_types: list[str] = field(default_factory=list)
    price_sensitivity: float = 0.5  # 0.0 (insensitive) to 1.0 (very sensitive)
    pace_preference: str = "moderate"  # "relaxed", "moderate", "intensive"

    # Running state (updated during simulation)
    budget_spent_eur: float = 0.0
    items_visited_today: int = 0
    current_day: int = 1
    simulated_hour: int = 9  # Start at 9am

    @property
    def trip_end_date(self) -> date:
        return self.trip_start_date + timedelta(days=self.trip_duration_days - 1)

    @property
    def total_budget(self) -> float:
        return self.daily_budget_eur * self.trip_duration_days

    @property
    def budget_remaining(self) -> float:
        return max(0, self.total_budget - self.budget_spent_eur)

    @property
    def budget_used_percent(self) -> float:
        return (self.budget_spent_eur / self.total_budget * 100) if self.total_budget > 0 else 0


def create_persona_templates() -> dict[str, UserPersona]:
    """Create persona templates with dates relative to today."""
    base_date = date.today() + timedelta(days=random.randint(7, 30))

    return {
        "budget_backpacker": UserPersona(
            name="Budget Backpacker",
            persona_type="budget",
            trip_duration_days=7,
            daily_budget_eur=45.0,
            party_size=1,
            has_children=False,
            mobility_constraints=False,
            trip_start_date=base_date,
            preferred_poi_types=["park", "monument", "church"],  # Free/cheap
            price_sensitivity=0.95,
            pace_preference="intensive",
        ),
        "luxury_couple": UserPersona(
            name="Luxury Couple",
            persona_type="luxury",
            trip_duration_days=4,
            daily_budget_eur=400.0,
            party_size=2,
            has_children=False,
            mobility_constraints=False,
            trip_start_date=base_date,
            preferred_poi_types=["museum", "theater", "building"],
            price_sensitivity=0.1,
            pace_preference="relaxed",
        ),
        "family_vacation": UserPersona(
            name="Family with Kids",
            persona_type="family",
            trip_duration_days=5,
            daily_budget_eur=180.0,
            party_size=4,
            has_children=True,
            mobility_constraints=False,
            trip_start_date=base_date,
            preferred_poi_types=["park", "museum", "monument"],
            price_sensitivity=0.6,
            pace_preference="moderate",
        ),
        "cultural_explorer": UserPersona(
            name="Cultural Explorer",
            persona_type="cultural",
            trip_duration_days=10,
            daily_budget_eur=120.0,
            party_size=1,
            has_children=False,
            mobility_constraints=False,
            trip_start_date=base_date,
            preferred_poi_types=["church", "museum", "monument", "building"],
            price_sensitivity=0.4,
            pace_preference="moderate",
        ),
        "senior_traveler": UserPersona(
            name="Senior Traveler",
            persona_type="senior",
            trip_duration_days=6,
            daily_budget_eur=150.0,
            party_size=2,
            has_children=False,
            mobility_constraints=True,
            trip_start_date=base_date,
            preferred_poi_types=["church", "museum", "park"],
            price_sensitivity=0.5,
            pace_preference="relaxed",
        ),
    }


# =============================================================================
# Timing Profiles
# =============================================================================


@dataclass
class TimingProfile:
    """Defines timing characteristics for different user activities."""

    # Reading/absorbing content (POI details, descriptions)
    reading_min: float = 15.0
    reading_max: float = 90.0

    # Quick navigation between screens
    navigation_min: float = 0.5
    navigation_max: float = 2.0

    # Decision pauses (thinking before action)
    decision_min: float = 5.0
    decision_max: float = 20.0

    # After sending chat, waiting for and reading response
    chat_response_min: float = 8.0
    chat_response_max: float = 25.0

    # Comparison viewing (looking at multiple items)
    comparison_min: float = 10.0
    comparison_max: float = 40.0

    # Quick browse (scrolling through list)
    browse_min: float = 3.0
    browse_max: float = 12.0


# Predefined timing profiles
TIMING_PROFILES = {
    "realistic": TimingProfile(),
    "quick": TimingProfile(
        reading_min=2.0, reading_max=8.0,
        navigation_min=0.3, navigation_max=1.0,
        decision_min=1.0, decision_max=4.0,
        chat_response_min=2.0, chat_response_max=6.0,
        comparison_min=2.0, comparison_max=6.0,
        browse_min=1.0, browse_max=3.0,
    ),
    "demo": TimingProfile(
        reading_min=5.0, reading_max=15.0,
        navigation_min=0.5, navigation_max=1.5,
        decision_min=2.0, decision_max=6.0,
        chat_response_min=3.0, chat_response_max=8.0,
        comparison_min=3.0, comparison_max=10.0,
        browse_min=2.0, browse_max=5.0,
    ),
}


# =============================================================================
# Journey Phases and Arcs
# =============================================================================


class JourneyPhase(str, Enum):
    """Phases of a simulated user journey."""

    BROWSING = "browsing"  # Home -> Explore
    RESEARCHING = "researching"  # POI details
    PLANNING = "planning"  # Itinerary building
    BOOKING = "booking"  # Booking flow
    CHATTING = "chatting"  # AI interaction
    COMPARING = "comparing"  # POI comparison


class JourneyArc(str, Enum):
    """High-level user journey patterns."""

    DISCOVERY = "discovery"  # Browse -> research -> compare -> decide
    EXECUTION = "execution"  # Planning -> booking -> confirming
    PROBLEM_SOLVING = "problem"  # Hit constraint -> chat -> adjust
    DEEP_DIVE = "deep_dive"  # Research single POI extensively
    COMPARISON = "comparison"  # Compare multiple similar POIs


# Arc-aware transition weights: {arc: {phase: [(next_phase, weight), ...]}}
ARC_TRANSITIONS: dict[JourneyArc, dict[JourneyPhase, list[tuple[JourneyPhase, float]]]] = {
    JourneyArc.DISCOVERY: {
        JourneyPhase.BROWSING: [
            (JourneyPhase.RESEARCHING, 0.7),
            (JourneyPhase.BROWSING, 0.3),
        ],
        JourneyPhase.RESEARCHING: [
            (JourneyPhase.RESEARCHING, 0.3),
            (JourneyPhase.COMPARING, 0.35),
            (JourneyPhase.PLANNING, 0.2),
            (JourneyPhase.CHATTING, 0.15),
        ],
        JourneyPhase.COMPARING: [
            (JourneyPhase.RESEARCHING, 0.4),
            (JourneyPhase.PLANNING, 0.35),
            (JourneyPhase.CHATTING, 0.25),
        ],
        JourneyPhase.PLANNING: [
            (JourneyPhase.BROWSING, 0.4),
            (JourneyPhase.RESEARCHING, 0.3),
            (JourneyPhase.BOOKING, 0.3),
        ],
        JourneyPhase.CHATTING: [
            (JourneyPhase.RESEARCHING, 0.5),
            (JourneyPhase.PLANNING, 0.3),
            (JourneyPhase.BROWSING, 0.2),
        ],
        JourneyPhase.BOOKING: [
            (JourneyPhase.PLANNING, 0.5),
            (JourneyPhase.BROWSING, 0.5),
        ],
    },
    JourneyArc.EXECUTION: {
        JourneyPhase.PLANNING: [
            (JourneyPhase.BOOKING, 0.5),
            (JourneyPhase.PLANNING, 0.3),
            (JourneyPhase.CHATTING, 0.2),
        ],
        JourneyPhase.BOOKING: [
            (JourneyPhase.PLANNING, 0.4),
            (JourneyPhase.BOOKING, 0.3),
            (JourneyPhase.BROWSING, 0.3),
        ],
        JourneyPhase.CHATTING: [
            (JourneyPhase.BOOKING, 0.5),
            (JourneyPhase.PLANNING, 0.5),
        ],
        JourneyPhase.BROWSING: [
            (JourneyPhase.PLANNING, 0.7),
            (JourneyPhase.RESEARCHING, 0.3),
        ],
        JourneyPhase.RESEARCHING: [
            (JourneyPhase.PLANNING, 0.6),
            (JourneyPhase.BOOKING, 0.4),
        ],
        JourneyPhase.COMPARING: [
            (JourneyPhase.PLANNING, 0.7),
            (JourneyPhase.BOOKING, 0.3),
        ],
    },
    JourneyArc.PROBLEM_SOLVING: {
        JourneyPhase.CHATTING: [
            (JourneyPhase.PLANNING, 0.4),
            (JourneyPhase.RESEARCHING, 0.3),
            (JourneyPhase.CHATTING, 0.3),
        ],
        JourneyPhase.PLANNING: [
            (JourneyPhase.CHATTING, 0.4),
            (JourneyPhase.RESEARCHING, 0.3),
            (JourneyPhase.COMPARING, 0.3),
        ],
        JourneyPhase.RESEARCHING: [
            (JourneyPhase.CHATTING, 0.5),
            (JourneyPhase.PLANNING, 0.3),
            (JourneyPhase.BROWSING, 0.2),
        ],
        JourneyPhase.BROWSING: [
            (JourneyPhase.CHATTING, 0.6),
            (JourneyPhase.RESEARCHING, 0.4),
        ],
        JourneyPhase.COMPARING: [
            (JourneyPhase.CHATTING, 0.5),
            (JourneyPhase.PLANNING, 0.5),
        ],
        JourneyPhase.BOOKING: [
            (JourneyPhase.CHATTING, 0.7),
            (JourneyPhase.PLANNING, 0.3),
        ],
    },
    JourneyArc.DEEP_DIVE: {
        JourneyPhase.RESEARCHING: [
            (JourneyPhase.RESEARCHING, 0.4),
            (JourneyPhase.CHATTING, 0.4),
            (JourneyPhase.PLANNING, 0.2),
        ],
        JourneyPhase.CHATTING: [
            (JourneyPhase.RESEARCHING, 0.6),
            (JourneyPhase.CHATTING, 0.3),
            (JourneyPhase.PLANNING, 0.1),
        ],
        JourneyPhase.PLANNING: [
            (JourneyPhase.RESEARCHING, 0.5),
            (JourneyPhase.BOOKING, 0.3),
            (JourneyPhase.BROWSING, 0.2),
        ],
        JourneyPhase.BROWSING: [
            (JourneyPhase.RESEARCHING, 0.8),
            (JourneyPhase.BROWSING, 0.2),
        ],
        JourneyPhase.COMPARING: [
            (JourneyPhase.RESEARCHING, 0.7),
            (JourneyPhase.CHATTING, 0.3),
        ],
        JourneyPhase.BOOKING: [
            (JourneyPhase.RESEARCHING, 0.5),
            (JourneyPhase.PLANNING, 0.5),
        ],
    },
    JourneyArc.COMPARISON: {
        JourneyPhase.COMPARING: [
            (JourneyPhase.RESEARCHING, 0.4),
            (JourneyPhase.COMPARING, 0.3),
            (JourneyPhase.CHATTING, 0.2),
            (JourneyPhase.PLANNING, 0.1),
        ],
        JourneyPhase.RESEARCHING: [
            (JourneyPhase.COMPARING, 0.5),
            (JourneyPhase.RESEARCHING, 0.3),
            (JourneyPhase.CHATTING, 0.2),
        ],
        JourneyPhase.CHATTING: [
            (JourneyPhase.COMPARING, 0.5),
            (JourneyPhase.RESEARCHING, 0.3),
            (JourneyPhase.PLANNING, 0.2),
        ],
        JourneyPhase.PLANNING: [
            (JourneyPhase.COMPARING, 0.4),
            (JourneyPhase.BOOKING, 0.3),
            (JourneyPhase.BROWSING, 0.3),
        ],
        JourneyPhase.BROWSING: [
            (JourneyPhase.COMPARING, 0.6),
            (JourneyPhase.RESEARCHING, 0.4),
        ],
        JourneyPhase.BOOKING: [
            (JourneyPhase.PLANNING, 0.5),
            (JourneyPhase.COMPARING, 0.5),
        ],
    },
}


# =============================================================================
# Contextual Chat Templates
# =============================================================================


CONTEXTUAL_CHAT_TEMPLATES = {
    "time_constraint": [
        "I only have {hours} hours left today. Can I fit {poi_name} in?",
        "Is {poi_name} worth it if I only have {time_remaining}?",
        "What's essential to see at {poi_name} in under {hours} hours?",
        "Should I rush through {poi_name} or skip it given my time?",
    ],
    "budget_constraint": [
        "Is the skip-the-line ticket worth the extra {price_diff}?",
        "Are there any free days or discounts for {poi_name}?",
        "Is {poi_name} worth {price} for a {duration} minute visit?",
        "I have {budget_remaining} left for the trip. What should I prioritize?",
        "Can I see {poi_name} on a budget?",
    ],
    "family_specific": [
        "Is {poi_name} good for kids?",
        "Are strollers allowed inside {poi_name}?",
        "What's the best time to visit {poi_name} with young children?",
        "Any kid-friendly dining options near {poi_name}?",
        "Will my kids find {poi_name} interesting or will they get bored?",
    ],
    "accessibility": [
        "Is {poi_name} wheelchair accessible?",
        "How much walking is required at {poi_name}?",
        "Are there places to rest inside {poi_name}?",
        "Can someone with mobility issues enjoy {poi_name}?",
    ],
    "comparison": [
        "Between {poi_1} and {poi_2}, which is better for {criteria}?",
        "Should I do {poi_1} in the morning or afternoon compared to {poi_2}?",
        "If I can only pick one: {poi_1} or {poi_2}?",
        "{poi_1} vs {poi_2} - which has shorter queues?",
        "Is {poi_1} more impressive than {poi_2}?",
    ],
    "logistics": [
        "What's the best way to get from {poi_1} to {poi_2}?",
        "Should I book {poi_name} tickets in advance or on-site?",
        "Is there a combined ticket for {poi_1} and {poi_2}?",
        "What's the best order to visit {poi_1}, {poi_2}, and {poi_3}?",
    ],
    "deep_knowledge": [
        "What's the historical significance of {poi_name}?",
        "Why was {poi_name} built in {style} style?",
        "What happened to {poi_name} during World War II?",
        "Tell me something surprising about {poi_name}.",
        "What's the story behind {poi_name}'s most famous feature?",
    ],
    "planning": [
        "How should I order my visits for today?",
        "Can I fit {count} attractions in one day?",
        "What's a good lunch spot between {poi_1} and {poi_2}?",
        "What time should I start my day to see everything?",
        "Is my itinerary too ambitious for day {day}?",
    ],
    "booking": [
        "Do I need to book {poi_name} in advance?",
        "Are guided tours at {poi_name} worth it?",
        "What's included in the {poi_name} ticket?",
        "Can I cancel my {poi_name} reservation?",
        "Is there a discount for groups of {party_size}?",
    ],
}

# Legacy questions (fallback)
LEGACY_CHAT_QUESTIONS = {
    "poi_general": [
        "What should I know before visiting?",
        "How long should I spend here?",
        "What's the best time to visit?",
        "Is it worth the ticket price?",
    ],
    "poi_specific": [
        "What's the history behind {poi_name}?",
        "What makes {poi_name} special?",
        "Any tips for visiting {poi_name}?",
    ],
    "city_exploration": [
        "What are the must-see attractions in {city_name}?",
        "Local food recommendations in {city_name}?",
        "How many days do I need in {city_name}?",
    ],
}


# =============================================================================
# Simulation State
# =============================================================================


@dataclass
class SimulationState:
    """Current state of the simulation."""

    current_phase: JourneyPhase = JourneyPhase.BROWSING
    current_arc: JourneyArc = JourneyArc.DISCOVERY
    arc_started_at: int = 0  # Action count when arc started

    current_city: City | None = None
    current_poi: POI | None = None
    current_poi_mock_data: dict[str, Any] = field(default_factory=dict)

    viewed_pois: list[POI] = field(default_factory=list)
    trip_pois: list[POI] = field(default_factory=list)
    favorite_pois: list[POI] = field(default_factory=list)  # POIs to return to

    conversation_history: list[dict[str, str]] = field(default_factory=list)

    action_count: int = 0
    start_time: datetime | None = None


@dataclass
class SimulationConfig:
    """Configuration for the simulation."""

    duration_seconds: int = 180
    omen_ws_url: str = "ws://localhost:8100/ws"
    verbose: bool = False
    timing_profile: str = "realistic"
    persona_name: str | None = None  # None = random
    initial_arc: str | None = None  # None = random
    starting_day: int = 1


# =============================================================================
# Activity Simulator
# =============================================================================


class ActivitySimulator:
    """Simulates realistic user activity for Omen dashboard testing."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.omen_client: OmenClient | None = None
        self.state = SimulationState()

        # Set up persona
        templates = create_persona_templates()
        if config.persona_name and config.persona_name in templates:
            self.persona = templates[config.persona_name]
        else:
            self.persona = random.choice(list(templates.values()))

        self.persona.current_day = config.starting_day

        # Set up timing profile
        self.timing = TIMING_PROFILES.get(config.timing_profile, TIMING_PROFILES["realistic"])

        # Data caches
        self._cities: list[City] = []
        self._pois_by_city: dict[str, list[POI]] = {}

    async def _load_data(self) -> None:
        """Load cities and POIs from database."""
        async with async_session_maker() as session:
            result = await session.execute(select(City))
            self._cities = list(result.scalars().all())

            if not self._cities:
                raise RuntimeError("No cities found in database. Run seed scripts first.")

            for city in self._cities:
                result = await session.execute(
                    select(POI).where(POI.city_id == city.id)
                )
                pois = list(result.scalars().all())
                if pois:
                    self._pois_by_city[str(city.id)] = pois

        logger.info(
            f"Loaded {len(self._cities)} cities with "
            f"{sum(len(p) for p in self._pois_by_city.values())} POIs"
        )

    async def connect(self) -> bool:
        """Connect to Omen."""
        try:
            self.omen_client = OmenClient(url=self.config.omen_ws_url)
            success = await self.omen_client.connect()
            if success:
                logger.info(f"Connected to Omen at {self.config.omen_ws_url}")
            return success
        except Exception as e:
            logger.error(f"Failed to connect to Omen: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Omen."""
        if self.omen_client:
            await self.omen_client.disconnect()

    async def run(self) -> None:
        """Run the simulation for configured duration."""
        await self._load_data()

        self.state.start_time = datetime.now()
        end_time = self.state.start_time + timedelta(seconds=self.config.duration_seconds)

        # Initialize arc
        if self.config.initial_arc:
            try:
                self.state.current_arc = JourneyArc(self.config.initial_arc)
            except ValueError:
                self.state.current_arc = random.choice(list(JourneyArc))
        else:
            self.state.current_arc = random.choice(list(JourneyArc))

        self._print_header()

        try:
            while datetime.now() < end_time:
                action_type = await self._perform_action()

                # Get wait time based on action just performed
                wait_time = self._get_wait_time(action_type)
                await asyncio.sleep(wait_time)

                # Advance simulated time
                self.persona.simulated_hour = min(22, self.persona.simulated_hour + random.uniform(0.1, 0.3))

        except asyncio.CancelledError:
            logger.info("Simulation cancelled")
        finally:
            self._print_summary()

    def _print_header(self) -> None:
        """Print simulation header."""
        print(f"\n{'='*70}")
        print(f"  OMEN ACTIVITY SIMULATION - Enhanced")
        print(f"{'='*70}")
        print(f"  Persona:  {self.persona.name} ({self.persona.persona_type})")
        print(f"  Budget:   {self.persona.daily_budget_eur}/day x {self.persona.trip_duration_days} days = {self.persona.total_budget}")
        print(f"  Party:    {self.persona.party_size} {'(with kids)' if self.persona.has_children else ''}")
        print(f"  Pace:     {self.persona.pace_preference}")
        print(f"  Duration: {self.config.duration_seconds}s")
        print(f"  Timing:   {self.config.timing_profile}")
        print(f"  Arc:      {self.state.current_arc.value}")
        print(f"{'='*70}\n")

    def _print_summary(self) -> None:
        """Print simulation summary."""
        elapsed = datetime.now() - self.state.start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60)}:{int(elapsed.total_seconds() % 60):02d}"

        print(f"\n{'='*70}")
        print(f"  SIMULATION COMPLETE")
        print(f"{'='*70}")
        print(f"  Duration:       {elapsed_str}")
        print(f"  Total actions:  {self.state.action_count}")
        print(f"  POIs viewed:    {len(self.state.viewed_pois)}")
        print(f"  POIs in trip:   {len(self.state.trip_pois)}")
        print(f"  Budget spent:   {self.persona.budget_spent_eur:.2f} ({self.persona.budget_used_percent:.0f}%)")
        print(f"  Chat messages:  {len([m for m in self.state.conversation_history if m['role'] == 'user'])}")
        print(f"{'='*70}\n")

    def _get_wait_time(self, action_type: str) -> float:
        """Get realistic wait time based on action just performed."""
        t = self.timing

        if action_type == "poi_detail":
            return random.uniform(t.reading_min, t.reading_max)
        elif action_type == "navigation":
            return random.uniform(t.navigation_min, t.navigation_max)
        elif action_type == "chat":
            return random.uniform(t.chat_response_min, t.chat_response_max)
        elif action_type == "comparison":
            return random.uniform(t.comparison_min, t.comparison_max)
        elif action_type == "browse":
            return random.uniform(t.browse_min, t.browse_max)
        elif action_type == "decision":
            return random.uniform(t.decision_min, t.decision_max)
        else:
            return random.uniform(t.navigation_min, t.decision_max)

    async def _perform_action(self) -> str:
        """Perform a single simulated action. Returns action type for timing."""
        self.state.action_count += 1
        timestamp = self._get_timestamp()

        # Check for arc triggers before action
        new_arc = self._check_arc_triggers()
        if new_arc and new_arc != self.state.current_arc:
            self.state.current_arc = new_arc
            self.state.arc_started_at = self.state.action_count
            print(f"  [{timestamp}] ARC       -> {new_arc.value}")

        # Perform phase action
        action_type = "navigation"
        if self.state.current_phase == JourneyPhase.BROWSING:
            action_type = await self._action_browse(timestamp)
        elif self.state.current_phase == JourneyPhase.RESEARCHING:
            action_type = await self._action_research(timestamp)
        elif self.state.current_phase == JourneyPhase.PLANNING:
            action_type = await self._action_plan(timestamp)
        elif self.state.current_phase == JourneyPhase.BOOKING:
            action_type = await self._action_book(timestamp)
        elif self.state.current_phase == JourneyPhase.CHATTING:
            action_type = await self._action_chat(timestamp)
        elif self.state.current_phase == JourneyPhase.COMPARING:
            action_type = await self._action_compare(timestamp)

        # Transition to next phase
        self._transition_phase()

        return action_type

    def _get_timestamp(self) -> str:
        """Get elapsed timestamp string."""
        elapsed = datetime.now() - self.state.start_time
        return f"{int(elapsed.total_seconds() // 60)}:{int(elapsed.total_seconds() % 60):02d}"

    def _check_arc_triggers(self) -> JourneyArc | None:
        """Check if conditions trigger a new journey arc."""
        # Budget constraint trigger
        if self.persona.budget_used_percent > 70:
            if random.random() < 0.4:
                return JourneyArc.PROBLEM_SOLVING

        # Time constraint trigger (late in day)
        if self.persona.simulated_hour >= 17:
            if random.random() < 0.3:
                return JourneyArc.EXECUTION

        # Many items visited trigger
        if self.persona.items_visited_today >= 4:
            if random.random() < 0.3:
                return JourneyArc.EXECUTION

        # Similar POIs trigger comparison
        if len(self.state.viewed_pois) >= 3:
            recent_types = [p.poi_type for p in self.state.viewed_pois[-4:]]
            if recent_types and recent_types.count(recent_types[-1]) >= 2:
                if random.random() < 0.4:
                    return JourneyArc.COMPARISON

        # Return to favorite trigger
        if self.state.favorite_pois and random.random() < 0.15:
            return JourneyArc.DEEP_DIVE

        # Random arc change (low probability)
        if self.state.action_count - self.state.arc_started_at > 8:
            if random.random() < 0.2:
                return random.choice(list(JourneyArc))

        return None

    def _transition_phase(self) -> None:
        """Transition to next phase based on current arc."""
        arc_transitions = ARC_TRANSITIONS.get(self.state.current_arc, {})
        phase_transitions = arc_transitions.get(
            self.state.current_phase,
            [(JourneyPhase.BROWSING, 1.0)]
        )

        phases, weights = zip(*phase_transitions)
        self.state.current_phase = random.choices(phases, weights=weights)[0]

    # =========================================================================
    # Action Methods
    # =========================================================================

    async def _action_browse(self, timestamp: str) -> str:
        """Browse/explore cities with rich list context."""
        # Select city based on persona preferences or stick with current
        if not self.state.current_city or random.random() < 0.3:
            self.state.current_city = self._select_city()

        city = self.state.current_city
        city_id = str(city.id)
        pois = self._pois_by_city.get(city_id, [])

        # Filter by persona preferences
        if self.persona.preferred_poi_types:
            preferred = [p for p in pois if p.poi_type in self.persona.preferred_poi_types]
            if preferred:
                pois = preferred

        # Build list items for ComparisonLens
        visible_items = []
        for poi in pois[:6]:
            mock = get_mock_poi_data(poi.name, poi.poi_type, city.name)
            visible_items.append({
                "id": str(poi.id),
                "name": poi.name,
                "type": poi.poi_type,
                "price_eur": mock["poi_price_eur"],
                "rating": mock["poi_rating"],
                "duration_mins": poi.estimated_visit_duration,
            })

        filter_type = random.choice(self.persona.preferred_poi_types) if self.persona.preferred_poi_types else "all"

        metadata = {
            "city_name": city.name,
            "city_country": city.country,
            "filter_type": filter_type,
            "visible_items": visible_items,
            "total_results": len(pois),
            # UI state fields
            "scroll_position": random.uniform(0.0, 0.3),
            "viewport_width": 1920,
            "viewport_height": 1080,
            "is_typing": False,
            # User context
            "user_trip_start": self.persona.trip_start_date.isoformat(),
            "user_trip_end": self.persona.trip_end_date.isoformat(),
            "user_budget_remaining_eur": round(self.persona.budget_remaining, 2),
            "user_party_size": self.persona.party_size,
            "itinerary_day": self.persona.current_day,
        }

        await self.omen_client.send_context(
            screen=OmenScreen.EXPLORE,
            metadata=metadata,
        )

        print(f"  [{timestamp}] EXPLORE   {city.name} ({len(pois)} POIs, filter: {filter_type})")
        return "browse"

    async def _action_research(self, timestamp: str) -> str:
        """View POI details with rich metadata."""
        if not self.state.current_city:
            self.state.current_city = self._select_city()

        poi = self._select_poi()
        if not poi:
            return "navigation"

        self.state.current_poi = poi
        if poi not in self.state.viewed_pois:
            self.state.viewed_pois.append(poi)

        # Get mock data
        mock_data = get_mock_poi_data(poi.name, poi.poi_type, self.state.current_city.name)
        self.state.current_poi_mock_data = mock_data

        # Get time context
        time_ctx = get_simulated_current_time_context(
            mock_data["poi_opening_hours"],
            simulate_hour=int(self.persona.simulated_hour),
        )

        # Get warnings for WarningLens
        warnings = get_warning_triggers(
            mock_data,
            time_ctx,
            budget_remaining=self.persona.budget_remaining,
            party_size=self.persona.party_size,
        )

        metadata = {
            # POI details
            "poi_name": poi.name,
            "poi_city": self.state.current_city.name,
            "poi_country": self.state.current_city.country,
            "poi_type": poi.poi_type,
            "poi_visit_duration_mins": poi.estimated_visit_duration,
            "poi_year_built": poi.year_built,
            "poi_architect": poi.architect,
            "poi_architectural_style": poi.architectural_style,
            "poi_heritage_status": poi.heritage_status,
            # Mock data
            "poi_price_eur": mock_data["poi_price_eur"],
            "poi_price_skip_line_eur": mock_data["poi_price_skip_line_eur"],
            "poi_opening_hours": mock_data["poi_opening_hours"],
            "poi_rating": mock_data["poi_rating"],
            "poi_review_count": mock_data["poi_review_count"],
            "poi_crowd_level": mock_data["poi_crowd_level"],
            "poi_accessibility": mock_data["poi_accessibility"],
            "poi_best_time": mock_data["poi_best_time"],
            "poi_booking_required": mock_data["poi_booking_required"],
            # Time context
            "current_hour": time_ctx["current_hour"],
            "closing_soon": time_ctx["closing_soon"],
            "time_until_close_mins": time_ctx["time_until_close_mins"],
            "is_open": time_ctx["is_open"],
            # Warnings
            "active_warnings": [w["message"] for w in warnings[:2]],
            # User context
            "user_trip_start": self.persona.trip_start_date.isoformat(),
            "user_trip_end": self.persona.trip_end_date.isoformat(),
            "user_budget_remaining_eur": round(self.persona.budget_remaining, 2),
            "user_party_size": self.persona.party_size,
            "user_has_children": self.persona.has_children,
            "user_mobility_constraints": self.persona.mobility_constraints,
            # Itinerary context
            "itinerary_day": self.persona.current_day,
            "itinerary_items_today": self.persona.items_visited_today,
            "itinerary_total_items": len(self.state.trip_pois),
            # UI state
            "scroll_position": random.uniform(0.0, 0.8),
            "viewport_width": 1920,
            "viewport_height": 1080,
            "is_typing": False,
            # Conversation history for PredictionLens
            "conversation_history": self.state.conversation_history[-2:],
        }

        await self.omen_client.send_context(
            screen=OmenScreen.POI_DETAIL,
            metadata=metadata,
            selected_item_id=str(poi.id),
            selected_item_type="poi",
        )

        # Update persona state
        self.persona.items_visited_today += 1
        if mock_data["poi_price_eur"] and random.random() < 0.5:
            cost = mock_data["poi_price_eur"] * self.persona.party_size
            self.persona.budget_spent_eur += cost

        # Maybe add to favorites
        if mock_data["poi_rating"] > 4.5 and random.random() < 0.3:
            if poi not in self.state.favorite_pois:
                self.state.favorite_pois.append(poi)

        price_str = f"{mock_data['poi_price_eur']}EUR" if mock_data["poi_price_eur"] else "Free"
        print(f"  [{timestamp}] POI       {poi.name} ({price_str}, {mock_data['poi_rating']}/5)")

        return "poi_detail"

    async def _action_plan(self, timestamp: str) -> str:
        """Build itinerary with rich planning context."""
        # Add a viewed POI to trip
        if self.state.viewed_pois:
            poi = random.choice(self.state.viewed_pois)
            if poi not in self.state.trip_pois:
                self.state.trip_pois.append(poi)

        # Build itinerary items
        itinerary_items = []
        for poi in self.state.trip_pois[:6]:
            mock = get_mock_poi_data(poi.name, poi.poi_type, self.state.current_city.name if self.state.current_city else "Unknown")
            itinerary_items.append({
                "id": str(poi.id),
                "name": poi.name,
                "type": poi.poi_type,
                "duration_mins": poi.estimated_visit_duration,
                "price_eur": mock["poi_price_eur"],
            })

        # Calculate totals
        total_duration = sum(item["duration_mins"] for item in itinerary_items)
        total_cost = sum((item["price_eur"] or 0) * self.persona.party_size for item in itinerary_items)

        metadata = {
            "city_name": self.state.current_city.name if self.state.current_city else "Multiple",
            "trip_duration_days": self.persona.trip_duration_days,
            "current_day": self.persona.current_day,
            "items_planned": len(self.state.trip_pois),
            "itinerary_items": itinerary_items,
            "total_duration_mins": total_duration,
            "total_cost_eur": round(total_cost, 2),
            # User context
            "user_trip_start": self.persona.trip_start_date.isoformat(),
            "user_trip_end": self.persona.trip_end_date.isoformat(),
            "user_budget_remaining_eur": round(self.persona.budget_remaining, 2),
            "user_budget_used_percent": round(self.persona.budget_used_percent, 1),
            "user_party_size": self.persona.party_size,
            "user_pace_preference": self.persona.pace_preference,
            # Potential warnings
            "budget_exceeded": total_cost > self.persona.budget_remaining,
            "time_exceeded": total_duration > 8 * 60,  # > 8 hours
            # UI state
            "scroll_position": random.uniform(0.0, 0.5),
            "viewport_width": 1920,
            "viewport_height": 1080,
            "is_typing": False,
            # Conversation history
            "conversation_history": self.state.conversation_history[-2:],
        }

        await self.omen_client.send_context(
            screen=OmenScreen.ITINERARY,
            metadata=metadata,
        )

        print(f"  [{timestamp}] ITINERARY {len(self.state.trip_pois)} POIs ({total_duration}min, {total_cost:.0f}EUR)")
        return "decision"

    async def _action_book(self, timestamp: str) -> str:
        """Simulate booking flow with detailed context."""
        poi = self.state.current_poi or (random.choice(self.state.trip_pois) if self.state.trip_pois else None)
        if not poi:
            return "navigation"

        mock_data = get_mock_poi_data(poi.name, poi.poi_type, self.state.current_city.name if self.state.current_city else "Unknown")

        booking_type = random.choice(["standard", "skip_line", "guided_tour", "audio_guide"])
        base_price = mock_data["poi_price_eur"] or 15

        if booking_type == "skip_line":
            price = mock_data["poi_price_skip_line_eur"] or base_price * 1.8
        elif booking_type == "guided_tour":
            price = base_price * 2.5
        elif booking_type == "audio_guide":
            price = base_price + 8
        else:
            price = base_price

        total_price = price * self.persona.party_size

        metadata = {
            "poi_name": poi.name,
            "poi_type": poi.poi_type,
            "booking_type": booking_type,
            "party_size": self.persona.party_size,
            "unit_price_eur": round(price, 2),
            "total_price_eur": round(total_price, 2),
            "poi_rating": mock_data["poi_rating"],
            "poi_crowd_level": mock_data["poi_crowd_level"],
            # User context
            "user_budget_remaining_eur": round(self.persona.budget_remaining, 2),
            "budget_after_booking": round(self.persona.budget_remaining - total_price, 2),
            "booking_exceeds_budget": total_price > self.persona.budget_remaining,
            # UI state
            "scroll_position": 0.0,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "is_typing": False,
        }

        await self.omen_client.send_context(
            screen=OmenScreen.BOOKING,
            metadata=metadata,
            selected_item_id=str(poi.id),
            selected_item_type="booking",
        )

        print(f"  [{timestamp}] BOOKING   {booking_type} x{self.persona.party_size} = {total_price:.0f}EUR")
        return "decision"

    async def _action_chat(self, timestamp: str) -> str:
        """Send contextual chat message to Omen."""
        question = self._generate_contextual_question()

        # Record in conversation history
        self._record_chat(question)

        await self.omen_client.send_chat(content=question)

        display_q = question[:50] + "..." if len(question) > 50 else question
        print(f"  [{timestamp}] CHAT      \"{display_q}\"")

        return "chat"

    async def _action_compare(self, timestamp: str) -> str:
        """Compare POIs with rich comparison context."""
        if len(self.state.viewed_pois) < 2:
            self.state.current_phase = JourneyPhase.RESEARCHING
            return "navigation"

        # Select POIs to compare (prefer same type)
        pois_to_compare = []
        if self.state.current_poi:
            same_type = [p for p in self.state.viewed_pois if p.poi_type == self.state.current_poi.poi_type and p != self.state.current_poi]
            if same_type:
                pois_to_compare = [self.state.current_poi] + same_type[:2]

        if len(pois_to_compare) < 2:
            pois_to_compare = random.sample(self.state.viewed_pois, min(3, len(self.state.viewed_pois)))

        # Build comparison items
        compare_items = []
        for poi in pois_to_compare:
            mock = get_mock_poi_data(poi.name, poi.poi_type, self.state.current_city.name if self.state.current_city else "Unknown")
            compare_items.append({
                "id": str(poi.id),
                "name": poi.name,
                "type": poi.poi_type,
                "price_eur": mock["poi_price_eur"],
                "rating": mock["poi_rating"],
                "duration_mins": poi.estimated_visit_duration,
                "crowd_level": mock["poi_crowd_level"],
                "accessibility": mock["poi_accessibility"],
            })

        metadata = {
            "comparing_pois": [p["name"] for p in compare_items],
            "compare_items": compare_items,
            "comparison_count": len(compare_items),
            "comparison_type": pois_to_compare[0].poi_type if pois_to_compare else "mixed",
            # User context
            "user_budget_remaining_eur": round(self.persona.budget_remaining, 2),
            "user_party_size": self.persona.party_size,
            "user_has_children": self.persona.has_children,
            "user_mobility_constraints": self.persona.mobility_constraints,
            "user_price_sensitivity": self.persona.price_sensitivity,
            # UI state
            "scroll_position": 0.0,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "is_typing": False,
            # Conversation history
            "conversation_history": self.state.conversation_history[-2:],
        }

        await self.omen_client.send_context(
            screen=OmenScreen.COMPARE,
            metadata=metadata,
        )

        names = " vs ".join([p["name"][:15] for p in compare_items[:2]])
        print(f"  [{timestamp}] COMPARE   {names}")
        return "comparison"

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _select_city(self) -> City:
        """Select a city, preferring ones with POIs matching persona preferences."""
        if self.persona.preferred_poi_types:
            # Find cities with preferred POI types
            matching_cities = []
            for city in self._cities:
                pois = self._pois_by_city.get(str(city.id), [])
                if any(p.poi_type in self.persona.preferred_poi_types for p in pois):
                    matching_cities.append(city)
            if matching_cities:
                return random.choice(matching_cities)

        return random.choice(self._cities)

    def _select_poi(self) -> POI | None:
        """Select a POI based on persona preferences."""
        if not self.state.current_city:
            return None

        city_id = str(self.state.current_city.id)
        pois = self._pois_by_city.get(city_id, [])

        if not pois:
            # Try to find a city with POIs
            for city in self._cities:
                if str(city.id) in self._pois_by_city:
                    self.state.current_city = city
                    pois = self._pois_by_city[str(city.id)]
                    break

        if not pois:
            return None

        # Filter by preferences
        if self.persona.preferred_poi_types:
            preferred = [p for p in pois if p.poi_type in self.persona.preferred_poi_types]
            if preferred:
                pois = preferred

        # Occasionally return to a favorite
        if self.state.favorite_pois and random.random() < 0.2:
            return random.choice(self.state.favorite_pois)

        return random.choice(pois)

    def _record_chat(self, user_message: str, assistant_response: str = "") -> None:
        """Record chat exchange in conversation history."""
        self.state.conversation_history.append({
            "role": "user",
            "content": user_message,
        })
        if assistant_response:
            self.state.conversation_history.append({
                "role": "assistant",
                "content": assistant_response,
            })
        # Keep only last 4 messages (2 exchanges)
        self.state.conversation_history = self.state.conversation_history[-4:]

    def _generate_contextual_question(self) -> str:
        """Generate a question based on current persona state and context."""
        poi = self.state.current_poi
        city = self.state.current_city
        mock = self.state.current_poi_mock_data

        # Budget constraint questions
        if self.persona.budget_used_percent > 60 and random.random() < 0.4:
            if poi and mock:
                template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["budget_constraint"])
                return template.format(
                    poi_name=poi.name,
                    price=mock.get("poi_price_eur", 15),
                    price_diff=round((mock.get("poi_price_skip_line_eur") or 0) - (mock.get("poi_price_eur") or 0), 0),
                    budget_remaining=round(self.persona.budget_remaining, 0),
                    duration=poi.estimated_visit_duration,
                )

        # Time constraint questions
        if self.persona.simulated_hour >= 16 and random.random() < 0.3:
            if poi:
                hours_left = max(1, 20 - int(self.persona.simulated_hour))
                template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["time_constraint"])
                return template.format(
                    poi_name=poi.name,
                    hours=hours_left,
                    time_remaining=f"{hours_left} hours",
                )

        # Family-specific questions
        if self.persona.has_children and random.random() < 0.35:
            if poi:
                template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["family_specific"])
                return template.format(poi_name=poi.name)

        # Accessibility questions
        if self.persona.mobility_constraints and random.random() < 0.35:
            if poi:
                template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["accessibility"])
                return template.format(poi_name=poi.name)

        # Comparison questions
        if len(self.state.viewed_pois) >= 2 and random.random() < 0.3:
            recent = self.state.viewed_pois[-2:]
            criteria = random.choice(["photography", "history", "a quick visit", "avoiding crowds", "families"])
            template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["comparison"])
            return template.format(
                poi_1=recent[0].name,
                poi_2=recent[1].name,
                criteria=criteria,
            )

        # Planning questions
        if self.state.trip_pois and random.random() < 0.25:
            template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["planning"])
            pois = self.state.trip_pois[:3]
            return template.format(
                count=len(self.state.trip_pois),
                day=self.persona.current_day,
                poi_1=pois[0].name if len(pois) > 0 else "the museum",
                poi_2=pois[1].name if len(pois) > 1 else "the monument",
                poi_3=pois[2].name if len(pois) > 2 else "the church",
            )

        # Deep knowledge questions
        if poi and poi.architect and random.random() < 0.25:
            template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["deep_knowledge"])
            return template.format(
                poi_name=poi.name,
                style=poi.architectural_style or "unique",
            )

        # Booking questions
        if mock and mock.get("poi_booking_required") and random.random() < 0.25:
            template = random.choice(CONTEXTUAL_CHAT_TEMPLATES["booking"])
            return template.format(
                poi_name=poi.name if poi else "this attraction",
                party_size=self.persona.party_size,
            )

        # Fallback to legacy questions
        if poi:
            if random.random() < 0.6:
                template = random.choice(LEGACY_CHAT_QUESTIONS["poi_specific"])
                return template.format(poi_name=poi.name)
            else:
                return random.choice(LEGACY_CHAT_QUESTIONS["poi_general"])

        if city:
            template = random.choice(LEGACY_CHAT_QUESTIONS["city_exploration"])
            return template.format(city_name=city.name)

        return random.choice(LEGACY_CHAT_QUESTIONS["poi_general"])


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Omen activity simulation with personas and realistic timing"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=180,
        help="Duration in seconds (default: 180 = 3 minutes)",
    )
    parser.add_argument(
        "--persona",
        choices=list(create_persona_templates().keys()) + ["random"],
        default="random",
        help="User persona to simulate (default: random)",
    )
    parser.add_argument(
        "--arc",
        choices=[a.value for a in JourneyArc] + ["random"],
        default="random",
        help="Initial journey arc (default: random)",
    )
    parser.add_argument(
        "--timing",
        choices=list(TIMING_PROFILES.keys()),
        default="realistic",
        help="Timing profile: realistic (15-90s reads), quick (2-8s), demo (5-15s)",
    )
    parser.add_argument(
        "--quick-mode",
        action="store_true",
        help="Shortcut for --timing quick",
    )
    parser.add_argument(
        "--day",
        type=int,
        default=1,
        help="Starting day of trip (affects context)",
    )
    parser.add_argument(
        "--omen-url",
        type=str,
        default="ws://localhost:8100/ws",
        help="Omen WebSocket URL",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = SimulationConfig(
        duration_seconds=args.duration,
        omen_ws_url=args.omen_url,
        verbose=args.verbose,
        timing_profile="quick" if args.quick_mode else args.timing,
        persona_name=None if args.persona == "random" else args.persona,
        initial_arc=None if args.arc == "random" else args.arc,
        starting_day=args.day,
    )

    simulator = ActivitySimulator(config)

    if await simulator.connect():
        try:
            await simulator.run()
        finally:
            await simulator.disconnect()
    else:
        print("Failed to connect to Omen. Is the Omen server running?")
        print(f"Expected URL: {config.omen_ws_url}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
