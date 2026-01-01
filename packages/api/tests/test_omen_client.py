"""Unit tests for the Omen client module.

These tests verify the OmenClient class works correctly.
They use a mock WebSocket server, so Omen doesn't need to be running.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from travelers_api.clients.omen import (
    AssistantOutput,
    ContextUpdate,
    EngineStatus,
    OmenClient,
    OmenError,
    OmenScreen,
    OmenState,
    OmenTarget,
    StreamChunk,
    UserMessage,
)


class TestOmenModels:
    """Test Pydantic models."""

    def test_context_update_create(self):
        """Test ContextUpdate factory method."""
        update = ContextUpdate.create(
            screen=OmenScreen.POI_DETAIL,
            metadata={"poi_name": "Colosseum"},
            selected_item_id="poi-123",
            selected_item_type="poi",
        )

        assert update.type == "context_update"
        assert update.ui_state["screen"] == "poi_detail"
        assert update.ui_state["metadata"]["poi_name"] == "Colosseum"
        assert update.ui_state["selected_item_id"] == "poi-123"
        assert update.timestamp > 0

    def test_user_message(self):
        """Test UserMessage model."""
        msg = UserMessage(content="Hello", conversation_id="conv-1")

        assert msg.type == "user_message"
        assert msg.content == "Hello"
        assert msg.conversation_id == "conv-1"
        assert msg.timestamp is not None

    def test_engine_status(self):
        """Test EngineStatus model."""
        status = EngineStatus(
            fast_model_ready=True,
            quality_model_ready=False,
            background_cycle_active=True,
        )

        assert status.fast_model_ready is True
        assert status.quality_model_ready is False

    def test_assistant_output(self):
        """Test AssistantOutput model."""
        output = AssistantOutput(
            target=OmenTarget.SIDEBAR,
            content="Test insight",
            confidence=0.85,
            lens_source="proactive_tip",
            timestamp=1234567890.0,
        )

        assert output.target == OmenTarget.SIDEBAR
        assert output.content == "Test insight"
        assert output.confidence == 0.85

    def test_stream_chunk(self):
        """Test StreamChunk model."""
        chunk = StreamChunk(
            content="Hello",
            done=False,
            conversation_id="conv-1",
        )

        assert chunk.content == "Hello"
        assert chunk.done is False


class TestOmenState:
    """Test OmenState management."""

    def test_initial_state(self):
        """Test default state values."""
        state = OmenState()

        assert state.is_connected is False
        assert state.is_ready is False
        assert state.sidebar_insights == []
        assert state.ambient_message is None
        assert state.chat_response == ""
        assert state.is_streaming is False
        assert state.last_error is None

    def test_state_update(self):
        """Test state can be updated."""
        state = OmenState()
        state.is_connected = True
        state.is_ready = True

        assert state.is_connected is True
        assert state.is_ready is True


class TestOmenClient:
    """Test OmenClient class."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return OmenClient(url="ws://localhost:8100/ws")

    def test_client_init(self, client):
        """Test client initialization."""
        assert client.url == "ws://localhost:8100/ws"
        assert client.is_connected is False
        assert client.is_ready is False

    def test_client_init_with_api_key(self):
        """Test client initialization with API key."""
        client = OmenClient(url="ws://localhost:8100/ws", api_key="test-key")
        assert "api_key=test-key" in client.url

    def test_state_property(self, client):
        """Test state property access."""
        state = client.state
        assert isinstance(state, OmenState)

    @pytest.mark.asyncio
    async def test_handle_engine_status(self, client):
        """Test engine_status message handling."""
        data = {
            "type": "engine_status",
            "fast_model_ready": True,
            "quality_model_ready": True,
            "background_cycle_active": True,
        }

        client._handle_engine_status(data)

        assert client.state.is_ready is True

    @pytest.mark.asyncio
    async def test_handle_engine_status_not_ready(self, client):
        """Test engine_status when models not ready."""
        data = {
            "type": "engine_status",
            "fast_model_ready": False,
            "quality_model_ready": False,
            "background_cycle_active": True,
        }

        client._handle_engine_status(data)

        assert client.state.is_ready is False

    @pytest.mark.asyncio
    async def test_handle_assistant_output_sidebar(self, client):
        """Test sidebar assistant_output handling."""
        data = {
            "target": "sidebar",
            "content": "Test insight",
            "confidence": 0.9,
            "lens_source": "test",
            "timestamp": 1234567890.0,
        }

        client._handle_assistant_output(data)

        assert len(client.state.sidebar_insights) == 1
        assert client.state.sidebar_insights[0].content == "Test insight"

    @pytest.mark.asyncio
    async def test_handle_assistant_output_max_insights(self, client):
        """Test sidebar respects max insights limit."""
        for i in range(10):
            data = {
                "target": "sidebar",
                "content": f"Insight {i}",
                "confidence": 0.9,
                "lens_source": "test",
                "timestamp": 1234567890.0 + i,
            }
            client._handle_assistant_output(data)

        # Should only keep last 5
        assert len(client.state.sidebar_insights) == 5
        assert client.state.sidebar_insights[-1].content == "Insight 9"

    @pytest.mark.asyncio
    async def test_handle_assistant_output_ambient(self, client):
        """Test ambient assistant_output handling."""
        data = {
            "target": "ambient",
            "content": "Ambient message",
            "confidence": 0.9,
            "lens_source": "test",
            "timestamp": 1234567890.0,
        }

        client._handle_assistant_output(data)

        assert client.state.ambient_message is not None
        assert client.state.ambient_message.content == "Ambient message"

    @pytest.mark.asyncio
    async def test_handle_stream_chunk(self, client):
        """Test stream_chunk handling."""
        # First chunk
        client._handle_stream_chunk({
            "content": "Hello ",
            "done": False,
        })

        assert client.state.chat_response == "Hello "
        assert client.state.is_streaming is True

        # Second chunk
        client._handle_stream_chunk({
            "content": "world!",
            "done": True,
        })

        assert client.state.chat_response == "Hello world!"
        assert client.state.is_streaming is False

    @pytest.mark.asyncio
    async def test_handle_error(self, client):
        """Test error message handling."""
        data = {
            "code": "model_unavailable",
            "message": "Model not ready",
        }

        client._handle_error(data)

        assert client.state.last_error is not None
        assert client.state.last_error.code == "model_unavailable"
        assert client.state.is_streaming is False

    def test_clear_sidebar_insights(self, client):
        """Test clearing sidebar insights."""
        # Add some insights
        client._state.sidebar_insights = [
            AssistantOutput(
                target=OmenTarget.SIDEBAR,
                content="Test",
                confidence=0.9,
                lens_source="test",
                timestamp=123.0,
            )
        ]

        client.clear_sidebar_insights()

        assert client.state.sidebar_insights == []

    def test_clear_ambient_message(self, client):
        """Test clearing ambient message."""
        client._state.ambient_message = AssistantOutput(
            target=OmenTarget.AMBIENT,
            content="Test",
            confidence=0.9,
            lens_source="test",
            timestamp=123.0,
        )

        client.clear_ambient_message()

        assert client.state.ambient_message is None


class TestOmenScreenEnum:
    """Test OmenScreen enum values."""

    def test_screen_values(self):
        """Test all screen enum values."""
        assert OmenScreen.HOME.value == "home"
        assert OmenScreen.EXPLORE.value == "explore"
        assert OmenScreen.POI_DETAIL.value == "poi_detail"
        assert OmenScreen.ITINERARY.value == "itinerary"
        assert OmenScreen.COMPARE.value == "compare"
        assert OmenScreen.BOOKING.value == "booking"
        assert OmenScreen.CHAT.value == "chat"


class TestOmenTargetEnum:
    """Test OmenTarget enum values."""

    def test_target_values(self):
        """Test all target enum values."""
        assert OmenTarget.SIDEBAR.value == "sidebar"
        assert OmenTarget.AMBIENT.value == "ambient"
        assert OmenTarget.CHAT.value == "chat"
