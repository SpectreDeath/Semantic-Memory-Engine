"""
Comprehensive tests for gateway/activation_streamer module.

Tests cover:
- StreamNode / StreamEdge dataclasses
- GephiWebSocketStreamer: connection, streaming, buffering, reconnection
- GephiHTTPStreamer: connection, streaming, buffering, batch
- ActivationMonitor: event handlers
- MCP tool wrappers
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from gateway.activation_streamer import (
    GephiHTTPStreamer,
    GephiWebSocketStreamer,
    ActivationMonitor,
    StreamNode,
    StreamEdge,
    stream_activations_tool,
    gephi_connection_tool,
)


# ============================================================================
# StreamNode / StreamEdge fixtures
# ============================================================================


def test_stream_node_creation():
    n = StreamNode(id="n1", label="test", size=2.0, color="#FF0000", x=10, y=20)
    assert n.id == "n1"
    assert n.label == "test"
    assert n.size == 2.0
    assert n.color == "#FF0000"
    assert n.x == 10
    assert n.y == 20
    assert n.attributes == {}


def test_stream_edge_creation():
    e = StreamEdge(source="a", target="b", weight=0.8, label="related")
    assert e.source == "a"
    assert e.target == "b"
    assert e.weight == 0.8
    assert e.label == "related"


# ============================================================================
# GephiWebSocketStreamer (mocked)
# ============================================================================


@pytest.mark.asyncio
class TestGephiWebSocketStreamer:
    """Test the WebSocket-based Gephi streamer with mocked websockets."""

    async def create_connected_streamer(self):
        """Helper to get a streamer with a mocked websocket."""
        streamer = GephiWebSocketStreamer()
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.close = AsyncMock()

        async def mock_connect(url):
            return mock_ws

        self.mock_ws = mock_ws
        self.patcher = patch(
            "gateway.activation_streamer.websockets.connect", side_effect=mock_connect
        )
        self.patcher.start()
        return streamer

    def teardown_method(self):
        if hasattr(self, "patcher"):
            self.patcher.stop()

    async def test_connect_success(self):
        streamer = await self.create_connected_streamer()
        result = await streamer.connect()
        assert result is True
        assert streamer.connected is True

    async def test_stream_node_when_disconnected_buffers(self):
        """When not connected, items should be buffered."""
        streamer = GephiWebSocketStreamer()
        streamer.connected = False
        node = StreamNode(id="n1", label="test")
        result = await streamer.stream_node(node)
        assert result is False
        assert len(streamer._buffer) == 1

    async def test_stream_node_success(self):
        streamer = await self.create_connected_streamer()
        await streamer.connect()
        node = StreamNode(id="n1", label="test")
        result = await streamer.stream_node(node)
        assert result is True
        assert streamer.stream_count == 1
        self.mock_ws.send.assert_awaited_once()

    async def test_stream_batch_mixed(self):
        streamer = await self.create_connected_streamer()
        await streamer.connect()
        nodes = [StreamNode(id=f"n{i}", label=f"node{i}") for i in range(3)]
        edges = [StreamEdge(source="n0", target="n1")]
        result = await streamer.stream_batch(nodes, edges)
        assert result["success"] == 4
        assert result["failed"] == 0

    async def test_disconnect(self):
        streamer = await self.create_connected_streamer()
        await streamer.connect()
        await streamer.disconnect()
        assert streamer.connected is False
        self.mock_ws.close.assert_awaited_once()


# ============================================================================
# GephiHTTPStreamer
# ============================================================================


class TestGephiHTTPStreamer:
    """Test the HTTP-based Gephi streamer with mocked requests."""

    def setup_method(self):
        self.streamer = GephiHTTPStreamer()

    def test_check_connection_success(self):
        with patch("gateway.activation_streamer.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            result = self.streamer.check_connection()
            assert result is True
            assert self.streamer.connected is True

    def test_check_connection_failure(self):
        with patch(
            "gateway.activation_streamer.requests.get", side_effect=Exception("network error")
        ):
            result = self.streamer.check_connection()
            assert result is False
            assert self.streamer.connected is False

    def test_stream_node_success(self):
        with patch("gateway.activation_streamer.requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            # Pre-establish connection to avoid check_connection call
            self.streamer.connected = True
            node = StreamNode(id="n1", label="test", color="#FF0000")
            result = self.streamer.stream_node(node)
            assert result is True
            assert self.streamer.stream_count == 1

    def test_stream_node_buffers_when_disconnected(self):
        """Items should buffer when no connection."""
        with patch.object(self.streamer, "check_connection", return_value=False):
            node = StreamNode(id="n1", label="test")
            result = self.streamer.stream_node(node)
            assert result is False
            assert len(self.streamer._buffer) == 1

    def test_stream_edge_buffers(self):
        with patch.object(self.streamer, "check_connection", return_value=False):
            edge = StreamEdge(source="a", target="b")
            result = self.streamer.stream_edge(edge)
            assert result is False
            assert len(self.streamer._buffer) == 1

    def test_batch_stream_partial_failure(self):
        with patch.object(self.streamer, "check_connection", return_value=False):
            nodes = [StreamNode(id=f"n{i}", label=f"node{i}") for i in range(3)]
            edges = [StreamEdge(source="n0", target="n1")]
            result = self.streamer.stream_batch(nodes, edges)
            assert result["success"] == 0
            assert result["failed"] == 4
            assert len(self.streamer._buffer) == 4

    def test_flush_buffer(self):
        """Buffered items are sent on reconnection."""
        self.streamer._buffer = [{"anType": "node"}, {"anType": "edge"}]
        with patch("gateway.activation_streamer.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            flushed = self.streamer._flush_buffer()
            assert flushed == 2
            assert len(self.streamer._buffer) == 0
            assert self.streamer.stream_count == 2

    def test_clear_graph(self):
        with patch("gateway.activation_streamer.requests.delete") as mock_del:
            mock_del.return_value.status_code = 200
            result = self.streamer.clear_graph()
            assert result is True

    def test_get_stats(self):
        stats = self.streamer.get_stats()
        assert "connected" in stats
        assert "stream_count" in stats
        assert "buffer_size" in stats
        assert "failed_count" in stats


# ============================================================================
# ActivationMonitor
# ============================================================================


@pytest.mark.asyncio
class TestActivationMonitor:
    """Test the activation monitoring wrapper."""

    async def test_start_stop_monitoring(self):
        streamer = MagicMock()
        streamer.connect = AsyncMock(return_value=True)
        streamer.disconnect = AsyncMock()

        monitor = ActivationMonitor(streamer=streamer)
        await monitor.start_monitoring()
        assert monitor.monitoring is True
        streamer.connect.assert_called_once()

        await monitor.stop_monitoring()
        assert monitor.monitoring is False
        streamer.disconnect.assert_called_once()

    async def test_on_layer_activation_ignored_when_not_monitoring(self):
        streamer = MagicMock()
        monitor = ActivationMonitor(streamer=streamer)
        monitor.monitoring = False
        await monitor.on_layer_activation(0, {"0": 0.5})
        streamer.stream_activation_update.assert_not_called()

    async def test_on_layer_activation_streams_all_neurons(self):
        streamer = MagicMock()
        streamer.stream_activation_update = AsyncMock()
        monitor = ActivationMonitor(streamer=streamer)
        monitor.monitoring = True

        await monitor.on_layer_activation(1, {"3": 0.8, "7": 0.2}, concept="test")

        assert streamer.stream_activation_update.call_count == 2

    async def test_on_triplet_extracted(self):
        streamer = MagicMock()
        streamer.stream_node = AsyncMock()
        streamer.stream_edge = AsyncMock()
        monitor = ActivationMonitor(streamer=streamer)
        monitor.monitoring = True

        triplets = [{"subject": "Alice", "target": "Bob", "relation": "knows", "confidence": 0.9}]
        await monitor.on_triplet_extracted(triplets, source_query="alice bob")

        assert streamer.stream_node.call_count == 2
        assert streamer.stream_edge.call_count == 1


# ============================================================================
# MCP Tool wrappers
# ============================================================================


class TestMCPTools:
    """Test MCP tool interface."""

    def test_stream_activations_tool_requires_websockets(self):
        """Returns error if websockets not installed."""
        with patch("gateway.activation_streamer.WEBSOCKETS_AVAILABLE", False):
            result = stream_activations_tool(activations=[{"value": 0.5}])
            assert result["status"] == "error"
            assert "websockets" in result["error"].lower()

    def test_gephi_connection_tool(self):
        """Test connection check returns expected fields."""
        with patch.object(GephiWebSocketStreamer, "connect", new=AsyncMock(return_value=True)):
            with patch.object(
                GephiWebSocketStreamer,
                "get_stats",
                return_value={
                    "connected": True,
                    "gephi_url": "ws://localhost:8080/workspace0",
                    "workspace": "workspace0",
                },
            ):
                result = gephi_connection_tool()
                assert "status" in result


# ============================================================================
# Color helper & stats
# ============================================================================


def test_activation_to_color():
    streamer = GephiWebSocketStreamer()
    assert streamer._activation_to_color(0.9) == "#FF0000"
    assert streamer._activation_to_color(0.6) == "#FF8800"
    assert streamer._activation_to_color(0.3) == "#00FF00"
    assert streamer._activation_to_color(0.1) == "#0000FF"


def test_websocket_streamer_stats_defaults():
    s = GephiWebSocketStreamer()
    stats = s.get_stats()
    assert stats["connected"] is False
    assert stats["stream_count"] == 0
    assert "reconnect_attempts" in stats
