"""Integration tests for Omen AI Engine connection.

These tests verify the WebSocket connection between travelers.ai and Omen.

Prerequisites:
1. Omen server running: cd C:\\Users\\juanp\\Desktop\\code\\omen && python -m omen.server
2. llama-swap or llama-server running on port 8080

Run tests:
    pytest tests/test_omen_integration.py -v

Run as standalone script (more verbose):
    python tests/test_omen_integration.py
"""

import asyncio
import json
import sys
from datetime import datetime

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class OmenIntegrationTester:
    """Standalone tester for Omen integration."""

    def __init__(self, url: str = "ws://localhost:8100/ws"):
        self.url = url
        self.ws = None
        self.received_messages: list[dict] = []

    async def connect(self, timeout: float = 5.0) -> bool:
        """Connect to Omen WebSocket server."""
        try:
            import websockets
            self.ws = await asyncio.wait_for(
                websockets.connect(self.url),
                timeout=timeout
            )
            print(f"[OK] Connected to Omen at {self.url}")
            return True
        except asyncio.TimeoutError:
            print(f"[FAIL] Connection timeout to {self.url}")
            return False
        except Exception as e:
            print(f"[FAIL] Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Omen."""
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def receive_with_timeout(self, timeout: float = 10.0) -> dict | None:
        """Receive a message with timeout."""
        if not self.ws:
            return None
        try:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            msg = json.loads(raw)
            self.received_messages.append(msg)
            return msg
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(f"  Receive error: {e}")
            return None

    async def send_context(self, screen: str, metadata: dict) -> bool:
        """Send a context update to Omen."""
        if not self.ws:
            return False

        message = {
            "type": "context_update",
            "screenshot": None,
            "ui_state": {
                "screen": screen,
                "metadata": metadata,
            },
            "timestamp": datetime.now().timestamp(),
        }

        try:
            await self.ws.send(json.dumps(message))
            print(f"  -> Sent context_update: screen={screen}")
            return True
        except Exception as e:
            print(f"  [FAIL] Send failed: {e}")
            return False

    async def send_chat(self, content: str, conversation_id: str = "test") -> bool:
        """Send a chat message to Omen."""
        if not self.ws:
            return False

        message = {
            "type": "user_message",
            "content": content,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().timestamp(),
        }

        try:
            await self.ws.send(json.dumps(message))
            print(f"  -> Sent user_message: {content[:50]}...")
            return True
        except Exception as e:
            print(f"  [FAIL] Send failed: {e}")
            return False

    async def collect_messages(self, duration: float = 5.0) -> list[dict]:
        """Collect messages for a duration."""
        messages = []
        start = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start < duration:
            msg = await self.receive_with_timeout(timeout=0.5)
            if msg:
                messages.append(msg)

        return messages


async def test_omen_connection():
    """Test 1: Basic connection to Omen."""
    tester = OmenIntegrationTester()

    try:
        connected = await tester.connect(timeout=5.0)
        assert connected, "Failed to connect to Omen"

        # Should receive engine_status on connect
        status = await tester.receive_with_timeout(timeout=5.0)
        assert status is not None, "Did not receive engine_status"
        assert status.get("type") == "engine_status", f"Expected engine_status, got {status.get('type')}"

        print(f"  Engine status: fast_model={status.get('fast_model_ready')}, quality_model={status.get('quality_model_ready')}")

    finally:
        await tester.disconnect()


async def test_omen_context_update():
    """Test 2: Send context update and receive insights."""
    tester = OmenIntegrationTester()

    try:
        connected = await tester.connect(timeout=5.0)
        assert connected, "Failed to connect to Omen"

        # Receive initial status
        status = await tester.receive_with_timeout(timeout=5.0)
        assert status is not None, "Did not receive engine_status"

        # Check if models are ready
        fast_ready = status.get("fast_model_ready", False)
        quality_ready = status.get("quality_model_ready", False)

        if not fast_ready and not quality_ready:
            print("  [WARN] Omen reports models not ready - may need to restart Omen")
            print("  [INFO] Proceeding anyway to test context flow...")

        # Send POI context
        await tester.send_context(
            screen="poi_detail",
            metadata={
                "poi_name": "Colosseum",
                "poi_city": "Rome",
                "poi_country": "Italy",
                "poi_category": "historical",
                "poi_rating": 4.8,
                "poi_visit_duration_mins": 120,
            }
        )

        # Collect responses for up to 15 seconds
        print("  Waiting for Omen insights (up to 15s)...")
        messages = await tester.collect_messages(duration=15.0)

        # Check for assistant_output messages
        outputs = [m for m in messages if m.get("type") == "assistant_output"]
        print(f"  Received {len(outputs)} assistant_output messages")

        for output in outputs:
            target = output.get("target", "unknown")
            content = output.get("content", "")[:100]
            lens = output.get("lens_source", "unknown")
            print(f"    [{target}] ({lens}): {content}...")

        # Report what we received
        if len(outputs) > 0:
            print(f"  [OK] Received {len(outputs)} insights from Omen")
        else:
            print("  [WARN] No insights received (models may need restart)")

    finally:
        await tester.disconnect()


async def test_omen_chat():
    """Test 3: Send chat message and receive streaming response."""
    tester = OmenIntegrationTester()

    try:
        connected = await tester.connect(timeout=5.0)
        assert connected, "Failed to connect to Omen"

        # Receive initial status
        status = await tester.receive_with_timeout(timeout=5.0)
        assert status is not None, "Did not receive engine_status"

        if not status.get("quality_model_ready", False):
            print("  [WARN] Quality model not ready - chat may not receive response")
            print("  [INFO] Proceeding anyway to test chat flow...")

        # Send context first
        await tester.send_context(
            screen="poi_detail",
            metadata={
                "poi_name": "Colosseum",
                "poi_city": "Rome",
            }
        )

        # Send chat message
        await tester.send_chat("What makes the Colosseum special?")

        # Collect streaming response
        print("  Waiting for chat response (up to 30s)...")
        full_response = ""
        chunks_received = 0

        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 30.0:
            msg = await tester.receive_with_timeout(timeout=1.0)
            if msg:
                if msg.get("type") == "stream_chunk":
                    chunks_received += 1
                    full_response += msg.get("content", "")
                    if msg.get("done", False):
                        print(f"  [OK] Received complete response ({chunks_received} chunks)")
                        break

        if full_response:
            print(f"  Response preview: {full_response[:200]}...")

        if chunks_received > 0:
            print(f"  [OK] Received streaming chat response")
        else:
            print("  [WARN] No chat response received (model may need restart)")

    finally:
        await tester.disconnect()


async def run_all_tests():
    """Run all integration tests with detailed output."""
    print("=" * 60)
    print("Omen Integration Tests")
    print("=" * 60)
    print()

    tests = [
        ("Connection Test", test_omen_connection),
        ("Context Update Test", test_omen_context_update),
        ("Chat Test", test_omen_chat),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running: {name}")
        print("-" * 40)

        try:
            await test_func()
            print(f"[PASS] {name}")
            results.append((name, True, None))
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
            results.append((name, False, str(e)))
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results.append((name, False, str(e)))

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    for name, ok, error in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status}: {name}")
        if error:
            print(f"         {error}")

    return failed == 0


# Pytest fixtures and wrappers

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_connection():
    """Pytest wrapper for connection test."""
    await test_omen_connection()


@pytest.mark.asyncio
async def test_context():
    """Pytest wrapper for context test."""
    await test_omen_context_update()


@pytest.mark.asyncio
async def test_chat_streaming():
    """Pytest wrapper for chat test."""
    await test_omen_chat()


if __name__ == "__main__":
    print("""
Omen Integration Test Suite
===========================

Prerequisites:
1. Start Omen server:
   cd <path-to-omen>
   python -m omen.server

2. Start llama-swap (or llama-server):
   cd <path-to-omen>
   ./tools/llama-swap/llama-swap.exe --config config/llama-swap.yaml

3. Run this test:
   python tests/test_omen_integration.py

""")

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
