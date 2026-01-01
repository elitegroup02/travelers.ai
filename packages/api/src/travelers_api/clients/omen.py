"""Omen AI Engine WebSocket client.

This client manages the WebSocket connection to the Omen real-time AI engine,
which provides contextual insights based on user navigation and actions.

See: omen/docs/TRAVELERS_INTEGRATION.md for the full protocol spec.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import websockets
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


# --- Message Types ---


class OmenScreen(str, Enum):
    """Valid screen values for context updates."""

    HOME = "home"
    EXPLORE = "explore"
    POI_DETAIL = "poi_detail"
    ITINERARY = "itinerary"
    COMPARE = "compare"
    BOOKING = "booking"
    CHAT = "chat"


class OmenTarget(str, Enum):
    """Where Omen wants the output displayed."""

    SIDEBAR = "sidebar"
    AMBIENT = "ambient"
    CHAT = "chat"


class EngineStatus(BaseModel):
    """Status message from Omen on connect."""

    fast_model_ready: bool
    quality_model_ready: bool
    background_cycle_active: bool


class AssistantOutput(BaseModel):
    """Proactive insight from Omen."""

    target: OmenTarget
    content: str
    confidence: float
    lens_source: str
    timestamp: float


class StreamChunk(BaseModel):
    """Streaming chat response chunk."""

    content: str
    done: bool
    conversation_id: str | None = None


class OmenError(BaseModel):
    """Error message from Omen."""

    code: str
    message: str


# --- Outbound Messages ---


class ContextUpdate(BaseModel):
    """Context update message to send to Omen."""

    type: str = "context_update"
    screenshot: None = None
    ui_state: dict[str, Any]
    timestamp: float

    @classmethod
    def create(
        cls,
        screen: OmenScreen,
        metadata: dict[str, Any],
        selected_item_id: str | None = None,
        selected_item_type: str | None = None,
    ) -> "ContextUpdate":
        """Factory method to create a context update."""
        ui_state = {
            "screen": screen.value,
            "metadata": metadata,
        }
        if selected_item_id:
            ui_state["selected_item_id"] = selected_item_id
        if selected_item_type:
            ui_state["selected_item_type"] = selected_item_type

        return cls(
            ui_state=ui_state,
            timestamp=datetime.now().timestamp(),
        )


class UserMessage(BaseModel):
    """User chat message to send to Omen."""

    type: str = "user_message"
    content: str
    conversation_id: str | None = None
    timestamp: float | None = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now().timestamp()
        super().__init__(**data)


# --- Client State ---


class OmenState(BaseModel):
    """Current state of the Omen connection."""

    is_connected: bool = False
    is_ready: bool = False
    sidebar_insights: list[AssistantOutput] = []
    ambient_message: AssistantOutput | None = None
    chat_response: str = ""
    is_streaming: bool = False
    last_error: OmenError | None = None

    class Config:
        arbitrary_types_allowed = True


# --- Callback Types ---

MessageCallback = Callable[[dict[str, Any]], None]
StateCallback = Callable[[OmenState], None]


class OmenClient:
    """WebSocket client for the Omen AI engine.

    This client maintains a persistent connection to Omen and handles:
    - Connection lifecycle (connect, reconnect, disconnect)
    - Sending context updates when users navigate
    - Receiving and processing AI insights
    - Streaming chat responses

    Usage:
        client = OmenClient("ws://localhost:8100/ws")
        await client.connect()

        # Send context when user views a POI
        await client.send_context(
            screen=OmenScreen.POI_DETAIL,
            metadata={
                "poi_name": "Colosseum",
                "poi_city": "Rome",
                "poi_country": "Italy",
            }
        )

        # Send a chat message
        await client.send_chat("Is the Colosseum worth visiting?")

        # Get current state
        state = client.state
        print(state.sidebar_insights)
    """

    MAX_SIDEBAR_INSIGHTS = 5
    RECONNECT_DELAY = 5.0
    MAX_RECONNECT_ATTEMPTS = 10

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        on_message: MessageCallback | None = None,
        on_state_change: StateCallback | None = None,
    ):
        """Initialize the Omen client.

        Args:
            url: WebSocket URL for Omen (e.g., ws://localhost:8100/ws)
            api_key: Optional API key for authentication
            on_message: Callback for raw messages (useful for proxying to frontend)
            on_state_change: Callback when state changes
        """
        self.url = url
        if api_key:
            self.url = f"{url}?api_key={api_key}"

        self._ws: websockets.WebSocketClientProtocol | None = None
        self._state = OmenState()
        self._on_message = on_message
        self._on_state_change = on_state_change
        self._receive_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._should_reconnect = True
        self._reconnect_attempts = 0
        self._ambient_clear_task: asyncio.Task | None = None

    @property
    def state(self) -> OmenState:
        """Get current client state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected to Omen."""
        return self._state.is_connected

    @property
    def is_ready(self) -> bool:
        """Check if Omen models are ready."""
        return self._state.is_ready

    async def connect(self) -> bool:
        """Connect to Omen.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            logger.info(f"Connecting to Omen at {self.url.split('?')[0]}...")
            self._ws = await websockets.connect(self.url)
            self._update_state(is_connected=True)
            self._reconnect_attempts = 0
            logger.info("Connected to Omen")

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())
            return True

        except (WebSocketException, OSError) as e:
            logger.warning(f"Failed to connect to Omen: {e}")
            self._update_state(is_connected=False, is_ready=False)
            return False

    async def disconnect(self) -> None:
        """Disconnect from Omen."""
        self._should_reconnect = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        self._update_state(is_connected=False, is_ready=False)
        logger.info("Disconnected from Omen")

    async def send_context(
        self,
        screen: OmenScreen,
        metadata: dict[str, Any],
        selected_item_id: str | None = None,
        selected_item_type: str | None = None,
    ) -> bool:
        """Send a context update to Omen.

        Args:
            screen: Current screen/page the user is on
            metadata: Context data relevant to the screen
            selected_item_id: ID of selected item (e.g., POI ID)
            selected_item_type: Type of selected item (e.g., "poi")

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self._ws:
            logger.warning("Cannot send context: not connected to Omen")
            return False

        message = ContextUpdate.create(
            screen=screen,
            metadata=metadata,
            selected_item_id=selected_item_id,
            selected_item_type=selected_item_type,
        )

        try:
            await self._ws.send(message.model_dump_json())
            logger.debug(f"Sent context update: screen={screen.value}")
            return True
        except WebSocketException as e:
            logger.error(f"Failed to send context: {e}")
            return False

    async def send_chat(
        self,
        content: str,
        conversation_id: str | None = None,
    ) -> bool:
        """Send a chat message to Omen.

        Args:
            content: The user's message
            conversation_id: Optional conversation ID for continuity

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self._ws:
            logger.warning("Cannot send chat: not connected to Omen")
            return False

        # Reset chat state for new message
        self._update_state(chat_response="", is_streaming=True)

        message = UserMessage(content=content, conversation_id=conversation_id)

        try:
            await self._ws.send(message.model_dump_json())
            logger.debug(f"Sent chat message: {content[:50]}...")
            return True
        except WebSocketException as e:
            logger.error(f"Failed to send chat: {e}")
            self._update_state(is_streaming=False)
            return False

    async def send_poi_context(
        self,
        poi_id: str,
        poi_name: str,
        poi_city: str,
        poi_country: str,
        poi_category: str | None = None,
        poi_price_eur: float | None = None,
        poi_rating: float | None = None,
        poi_opening_hours: str | None = None,
        poi_visit_duration_mins: int | None = None,
        user_trip_start: str | None = None,
        user_trip_end: str | None = None,
        user_budget_remaining_eur: float | None = None,
        itinerary_day: int | None = None,
        itinerary_items_today: int | None = None,
    ) -> bool:
        """Convenience method to send POI detail context.

        This is the most common context update - when a user views a POI.
        """
        metadata = {
            "poi_name": poi_name,
            "poi_city": poi_city,
            "poi_country": poi_country,
        }

        # Add optional fields if provided
        if poi_category:
            metadata["poi_category"] = poi_category
        if poi_price_eur is not None:
            metadata["poi_price_eur"] = poi_price_eur
        if poi_rating is not None:
            metadata["poi_rating"] = poi_rating
        if poi_opening_hours:
            metadata["poi_opening_hours"] = poi_opening_hours
        if poi_visit_duration_mins is not None:
            metadata["poi_visit_duration_mins"] = poi_visit_duration_mins
        if user_trip_start:
            metadata["user_trip_start"] = user_trip_start
        if user_trip_end:
            metadata["user_trip_end"] = user_trip_end
        if user_budget_remaining_eur is not None:
            metadata["user_budget_remaining_eur"] = user_budget_remaining_eur
        if itinerary_day is not None:
            metadata["itinerary_day"] = itinerary_day
        if itinerary_items_today is not None:
            metadata["itinerary_items_today"] = itinerary_items_today

        return await self.send_context(
            screen=OmenScreen.POI_DETAIL,
            metadata=metadata,
            selected_item_id=poi_id,
            selected_item_type="poi",
        )

    def clear_sidebar_insights(self) -> None:
        """Clear all sidebar insights."""
        self._update_state(sidebar_insights=[])

    def clear_ambient_message(self) -> None:
        """Clear the ambient message."""
        self._update_state(ambient_message=None)

    async def _receive_loop(self) -> None:
        """Background task to receive and process messages."""
        try:
            async for message in self._ws:
                await self._handle_message(message)
        except ConnectionClosed:
            logger.info("Omen connection closed")
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
        finally:
            self._update_state(is_connected=False, is_ready=False)
            if self._should_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect to Omen with exponential backoff."""
        while self._should_reconnect and self._reconnect_attempts < self.MAX_RECONNECT_ATTEMPTS:
            self._reconnect_attempts += 1
            delay = min(self.RECONNECT_DELAY * (2 ** (self._reconnect_attempts - 1)), 60)
            logger.info(
                f"Reconnecting to Omen in {delay}s "
                f"(attempt {self._reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS})"
            )
            await asyncio.sleep(delay)

            if await self.connect():
                return

        if self._reconnect_attempts >= self.MAX_RECONNECT_ATTEMPTS:
            logger.error("Max reconnection attempts reached, giving up")

    async def _handle_message(self, raw: str) -> None:
        """Process an incoming message from Omen."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Omen: {raw[:100]}")
            return

        msg_type = data.get("type")

        # Notify raw message callback (for proxying to frontend)
        if self._on_message:
            self._on_message(data)

        # Process by message type
        if msg_type == "engine_status":
            self._handle_engine_status(data)
        elif msg_type == "assistant_output":
            self._handle_assistant_output(data)
        elif msg_type == "stream_chunk":
            self._handle_stream_chunk(data)
        elif msg_type == "error":
            self._handle_error(data)
        else:
            logger.debug(f"Unknown message type from Omen: {msg_type}")

    def _handle_engine_status(self, data: dict) -> None:
        """Handle engine_status message."""
        status = EngineStatus(**data)
        is_ready = status.fast_model_ready and status.quality_model_ready
        self._update_state(is_ready=is_ready)
        logger.info(
            f"Omen status: fast={status.fast_model_ready}, "
            f"quality={status.quality_model_ready}, "
            f"bg_cycle={status.background_cycle_active}"
        )

    def _handle_assistant_output(self, data: dict) -> None:
        """Handle assistant_output message."""
        output = AssistantOutput(**data)

        if output.target == OmenTarget.SIDEBAR:
            # Add to sidebar, keeping max 5 insights
            insights = self._state.sidebar_insights.copy()
            insights.append(output)
            if len(insights) > self.MAX_SIDEBAR_INSIGHTS:
                insights = insights[-self.MAX_SIDEBAR_INSIGHTS :]
            self._update_state(sidebar_insights=insights)
            logger.debug(f"Sidebar insight: {output.content[:50]}...")

        elif output.target == OmenTarget.AMBIENT:
            self._update_state(ambient_message=output)
            # Auto-clear after 5 seconds
            if self._ambient_clear_task:
                self._ambient_clear_task.cancel()
            self._ambient_clear_task = asyncio.create_task(self._clear_ambient_after_delay())
            logger.debug(f"Ambient message: {output.content[:50]}...")

        elif output.target == OmenTarget.CHAT:
            # Add to chat response
            self._update_state(
                chat_response=self._state.chat_response + output.content,
            )

    def _handle_stream_chunk(self, data: dict) -> None:
        """Handle stream_chunk message."""
        chunk = StreamChunk(**data)
        new_response = self._state.chat_response + chunk.content
        self._update_state(
            chat_response=new_response,
            is_streaming=not chunk.done,
        )

    def _handle_error(self, data: dict) -> None:
        """Handle error message."""
        error = OmenError(**data)
        self._update_state(last_error=error, is_streaming=False)
        logger.error(f"Omen error [{error.code}]: {error.message}")

    async def _clear_ambient_after_delay(self) -> None:
        """Clear ambient message after 5 seconds."""
        await asyncio.sleep(5)
        self._update_state(ambient_message=None)

    def _update_state(self, **kwargs) -> None:
        """Update state and notify callback."""
        for key, value in kwargs.items():
            setattr(self._state, key, value)

        if self._on_state_change:
            self._on_state_change(self._state)


# --- Singleton instance ---

_client: OmenClient | None = None


async def get_omen_client() -> OmenClient | None:
    """Get the global Omen client instance.

    Returns None if Omen is not configured.
    """
    return _client


async def init_omen_client(url: str, api_key: str | None = None) -> OmenClient:
    """Initialize the global Omen client.

    Called during application startup.
    """
    global _client
    _client = OmenClient(url=url, api_key=api_key)
    await _client.connect()
    return _client


async def close_omen_client() -> None:
    """Close the global Omen client.

    Called during application shutdown.
    """
    global _client
    if _client:
        await _client.disconnect()
        _client = None
