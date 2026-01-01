"""Omen AI Engine integration router.

This router provides:
1. WebSocket proxy endpoint for frontend ↔ Omen communication
2. REST endpoints for Omen state and convenience operations
3. POI detail context auto-send when viewing POIs

The frontend connects to /api/v1/omen/ws and this router proxies
messages to/from the Omen server running on a separate port.
"""

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..clients.omen import (
    AssistantOutput,
    OmenClient,
    OmenError,
    OmenScreen,
    OmenState,
    OmenTarget,
    get_omen_client,
)
from ..core.config import get_settings
from ..core.database import get_db
from ..models.poi import POI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/omen", tags=["Omen AI"])


# --- Response Models ---


class OmenStatusResponse(BaseModel):
    """Omen connection status."""

    enabled: bool
    is_connected: bool
    is_ready: bool
    sidebar_insight_count: int
    has_ambient_message: bool
    is_streaming: bool
    last_error: OmenError | None = None


class SidebarInsightsResponse(BaseModel):
    """Current sidebar insights."""

    insights: list[AssistantOutput]


class ChatRequest(BaseModel):
    """Chat message request."""

    content: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response (for non-streaming)."""

    response: str
    is_complete: bool


class ContextRequest(BaseModel):
    """Manual context update request."""

    screen: OmenScreen
    metadata: dict[str, Any]
    selected_item_id: str | None = None
    selected_item_type: str | None = None


# --- Dependencies ---


async def require_omen() -> OmenClient:
    """Dependency that requires Omen to be enabled and connected."""
    settings = get_settings()
    if not settings.omen_enabled:
        raise HTTPException(status_code=503, detail="Omen AI is not enabled")

    client = await get_omen_client()
    if not client:
        raise HTTPException(status_code=503, detail="Omen client not initialized")

    return client


# --- REST Endpoints ---


@router.get("/status", response_model=OmenStatusResponse)
async def get_omen_status():
    """Get current Omen connection status.

    Returns whether Omen is enabled, connected, and ready to provide insights.
    """
    settings = get_settings()

    if not settings.omen_enabled:
        return OmenStatusResponse(
            enabled=False,
            is_connected=False,
            is_ready=False,
            sidebar_insight_count=0,
            has_ambient_message=False,
            is_streaming=False,
        )

    client = await get_omen_client()
    if not client:
        return OmenStatusResponse(
            enabled=True,
            is_connected=False,
            is_ready=False,
            sidebar_insight_count=0,
            has_ambient_message=False,
            is_streaming=False,
        )

    state = client.state
    return OmenStatusResponse(
        enabled=True,
        is_connected=state.is_connected,
        is_ready=state.is_ready,
        sidebar_insight_count=len(state.sidebar_insights),
        has_ambient_message=state.ambient_message is not None,
        is_streaming=state.is_streaming,
        last_error=state.last_error,
    )


@router.get("/insights", response_model=SidebarInsightsResponse)
async def get_sidebar_insights(client: OmenClient = Depends(require_omen)):
    """Get current sidebar insights.

    Returns up to 5 most recent AI insights for display in the sidebar.
    """
    return SidebarInsightsResponse(insights=client.state.sidebar_insights)


@router.delete("/insights")
async def clear_insights(client: OmenClient = Depends(require_omen)):
    """Clear all sidebar insights."""
    client.clear_sidebar_insights()
    return {"status": "cleared"}


@router.post("/context")
async def send_context(
    request: ContextRequest,
    client: OmenClient = Depends(require_omen),
):
    """Send a context update to Omen.

    This tells Omen what screen the user is viewing and provides
    relevant metadata for generating insights.
    """
    success = await client.send_context(
        screen=request.screen,
        metadata=request.metadata,
        selected_item_id=request.selected_item_id,
        selected_item_type=request.selected_item_type,
    )

    if not success:
        raise HTTPException(status_code=503, detail="Failed to send context to Omen")

    return {"status": "sent"}


@router.post("/context/poi/{poi_id}")
async def send_poi_context(
    poi_id: UUID,
    client: OmenClient = Depends(require_omen),
    db: AsyncSession = Depends(get_db),
    trip_start: str | None = Query(None, description="Trip start date (YYYY-MM-DD)"),
    trip_end: str | None = Query(None, description="Trip end date (YYYY-MM-DD)"),
    budget_remaining: float | None = Query(None, description="Remaining budget in EUR"),
    itinerary_day: int | None = Query(None, description="Current day of itinerary"),
    items_today: int | None = Query(None, description="Number of items planned for today"),
):
    """Send POI detail context to Omen.

    Automatically fetches POI data from the database and sends
    a rich context update to Omen for generating insights.

    This is a convenience endpoint - the frontend can call this
    when a user views a POI detail page.
    """
    # Fetch POI from database
    result = await db.execute(select(POI).where(POI.id == poi_id))
    poi = result.scalar_one_or_none()

    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")

    # Get city info for the POI
    city_name = poi.city.name if poi.city else "Unknown"
    country = poi.city.country if poi.city else "Unknown"

    success = await client.send_poi_context(
        poi_id=str(poi.id),
        poi_name=poi.name,
        poi_city=city_name,
        poi_country=country,
        poi_category=poi.poi_type,
        poi_rating=poi.data_quality_score,
        poi_visit_duration_mins=poi.estimated_visit_duration,
        user_trip_start=trip_start,
        user_trip_end=trip_end,
        user_budget_remaining_eur=budget_remaining,
        itinerary_day=itinerary_day,
        itinerary_items_today=items_today,
    )

    if not success:
        raise HTTPException(status_code=503, detail="Failed to send POI context to Omen")

    return {"status": "sent", "poi_name": poi.name}


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    client: OmenClient = Depends(require_omen),
    timeout: float = Query(30.0, description="Max seconds to wait for response"),
):
    """Send a chat message to Omen and wait for the response.

    This is a synchronous endpoint that waits for the full response.
    For streaming responses, use the WebSocket endpoint instead.
    """
    success = await client.send_chat(
        content=request.content,
        conversation_id=request.conversation_id,
    )

    if not success:
        raise HTTPException(status_code=503, detail="Failed to send chat to Omen")

    # Wait for response (poll state)
    elapsed = 0.0
    poll_interval = 0.1

    while elapsed < timeout:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        if not client.state.is_streaming:
            return ChatResponse(
                response=client.state.chat_response,
                is_complete=True,
            )

    # Timeout - return partial response
    return ChatResponse(
        response=client.state.chat_response,
        is_complete=False,
    )


# --- WebSocket Proxy ---


class WebSocketManager:
    """Manages frontend WebSocket connections and proxies to Omen."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Frontend client connected: {client_id}")

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        logger.info(f"Frontend client disconnected: {client_id}")

    async def broadcast_to_client(self, client_id: str, message: dict):
        """Send message to a specific frontend client."""
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client {client_id}: {e}")


ws_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_proxy(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
):
    """WebSocket proxy endpoint for frontend ↔ Omen communication.

    The frontend connects here, and messages are proxied to/from Omen.
    This allows the backend to:
    1. Enrich context with database data before forwarding
    2. Store/log conversation history
    3. Handle authentication centrally

    Query params:
        client_id: Unique identifier for this client connection
    """
    settings = get_settings()

    if not settings.omen_enabled:
        await websocket.close(code=4003, reason="Omen AI is not enabled")
        return

    omen_client = await get_omen_client()
    if not omen_client or not omen_client.is_connected:
        await websocket.close(code=4003, reason="Omen is not connected")
        return

    await ws_manager.connect(websocket, client_id)

    # Send initial status to frontend
    await websocket.send_json({
        "type": "engine_status",
        "fast_model_ready": omen_client.is_ready,
        "quality_model_ready": omen_client.is_ready,
        "background_cycle_active": True,
    })

    # Set up callback to forward Omen messages to this client
    def on_omen_message(msg: dict):
        asyncio.create_task(ws_manager.broadcast_to_client(client_id, msg))

    # Store original callback and add ours
    original_callback = omen_client._on_message
    omen_client._on_message = on_omen_message

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "context_update":
                # Forward context update to Omen
                ui_state = data.get("ui_state", {})
                screen = ui_state.get("screen", "home")
                metadata = ui_state.get("metadata", {})

                try:
                    screen_enum = OmenScreen(screen)
                except ValueError:
                    screen_enum = OmenScreen.HOME

                await omen_client.send_context(
                    screen=screen_enum,
                    metadata=metadata,
                    selected_item_id=ui_state.get("selected_item_id"),
                    selected_item_type=ui_state.get("selected_item_type"),
                )

            elif msg_type == "user_message":
                # Forward chat message to Omen
                await omen_client.send_chat(
                    content=data.get("content", ""),
                    conversation_id=data.get("conversation_id"),
                )

            else:
                logger.debug(f"Unknown message type from frontend: {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"Frontend client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        ws_manager.disconnect(client_id)
        # Restore original callback
        omen_client._on_message = original_callback
