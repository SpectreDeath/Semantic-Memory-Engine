"""
Real-time Activation Streaming - WebSocket/HTTP bridge to Gephi.

This is Step 2.2 of Phase 2 - creates a WebSocket bridge between the SME Operator
and Gephi's Streaming Plugin for real-time visualization.

Supports both WebSocket and HTTP Streaming Plugin modes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger("lawnmower.activation_streamer")

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets not installed - streaming disabled")


GEPHI_WS_URL = "ws://localhost:8080/workspace0"
GEPHI_HTTP_URL = "http://localhost:8080"
GEPHI_STREAM_URL = "http://localhost:8080/workspace0"


@dataclass
class StreamNode:
    """A node to stream to Gephi."""

    id: str
    label: str
    size: float = 1.0
    color: str = "#00FF00"
    x: float = 0.0
    y: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamEdge:
    """An edge to stream to Gephi."""

    source: str
    target: str
    weight: float = 1.0
    label: str = ""


class GephiWebSocketStreamer:
    """
    Streams activations to Gephi in real-time via WebSocket.

    Connects to Gephi's Graph Streaming plugin and pushes
    nodes/edges as the LLM processes forensic queries.
    """

    def __init__(self, gephi_url: str = GEPHI_WS_URL, workspace: str = "workspace0"):
        self.gephi_url = gephi_url.replace("workspace0", workspace)
        self.workspace = workspace
        self.websocket = None
        self.connected = False
        self.stream_count = 0

    async def connect(self) -> bool:
        """Connect to Gephi WebSocket."""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets not available")
            return False

        try:
            self.websocket = await websockets.connect(self.gephi_url)
            self.connected = True
            logger.info(f"Connected to Gephi: {self.gephi_url}")
            return True
        except Exception as e:
            logger.warning(f"Gephi connection failed: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Gephi."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False

    async def stream_node(self, node: StreamNode):
        """Stream a single node to Gephi."""
        if not self.connected:
            return

        gephi_node = {
            "anType": "node",
            "key": node.id,
            "attrs": {
                "label": node.label,
                "size": node.size,
                "r": int(node.color[1:3], 16),
                "g": int(node.color[3:5], 16),
                "b": int(node.color[5:7], 16),
                "x": node.x,
                "y": node.y,
                **node.attributes,
            },
        }

        await self.websocket.send(json.dumps(gephi_node))
        self.stream_count += 1

    async def stream_edge(self, edge: StreamEdge):
        """Stream a single edge to Gephi."""
        if not self.connected:
            return

        edge_id = f"{edge.source}-{edge.target}"
        gephi_edge = {
            "anType": "edge",
            "key": edge_id,
            "source": edge.source,
            "target": edge.target,
            "attrs": {
                "weight": edge.weight,
                "label": edge.label,
            },
        }

        await self.websocket.send(json.dumps(gephi_edge))
        self.stream_count += 1

    async def stream_batch(self, nodes: list[StreamNode], edges: list[StreamEdge]):
        """Stream a batch of nodes and edges."""
        if not self.connected:
            return

        for node in nodes:
            await self.stream_node(node)

        for edge in edges:
            await self.stream_edge(edge)

    async def stream_activation_update(
        self, layer: int, neuron: int, activation: float, concept: str = ""
    ):
        """Stream an activation update."""
        node_id = f"L{layer}_N{neuron}"

        node = StreamNode(
            id=node_id,
            label=concept or node_id,
            size=1.0 + activation * 10,
            color=self._activation_to_color(activation),
            attributes={
                "layer": layer,
                "neuron": neuron,
                "activation": activation,
            },
        )

        await self.stream_node(node)

    def _activation_to_color(self, activation: float) -> str:
        """Convert activation value to color."""
        if activation > 0.8:
            return "#FF0000"
        elif activation > 0.5:
            return "#FF8800"
        elif activation > 0.2:
            return "#00FF00"
        else:
            return "#0000FF"

    def get_stats(self) -> dict[str, Any]:
        """Get streaming statistics."""
        return {
            "connected": self.connected,
            "gephi_url": self.gephi_url,
            "workspace": self.workspace,
            "stream_count": self.stream_count,
        }


class GephiHTTPStreamer:
    """
    Streams to Gephi via HTTP (Streaming Plugin REST API).

    More reliable than WebSocket for many use cases.
    """

    def __init__(self, stream_url: str = GEPHI_STREAM_URL, workspace: str = "workspace0"):
        self.stream_url = stream_url.replace("workspace0", workspace)
        self.workspace = workspace
        self.connected = False
        self.stream_count = 0
        self._buffer = []

    def check_connection(self) -> bool:
        """Check if Gephi Streaming Plugin is available."""
        try:
            resp = requests.get(GEPHI_HTTP_URL, timeout=1)
            self.connected = resp.status_code < 500
            return self.connected
        except Exception:
            self.connected = False
            return False

    def stream_node(self, node: StreamNode) -> bool:
        """Stream a node via HTTP POST."""
        if not self.connected:
            if not self.check_connection():
                return False

        payload = {
            "anType": "node",
            "key": node.id,
            "attrs": {
                "label": node.label,
                "size": node.size,
                "r": int(node.color[1:3], 16) if len(node.color) > 1 else 0,
                "g": int(node.color[3:5], 16) if len(node.color) > 3 else 0,
                "b": int(node.color[5:7], 16) if len(node.color) > 5 else 0,
                "x": node.x,
                "y": node.y,
            },
        }
        payload["attrs"].update(node.attributes)

        try:
            resp = requests.post(
                f"{self.stream_url}/graph",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=1,
            )
            if resp.status_code in (200, 201):
                self.stream_count += 1
                return True
        except Exception:
            pass
        return False

    def stream_edge(self, edge: StreamEdge) -> bool:
        """Stream an edge via HTTP POST."""
        if not self.connected:
            if not self.check_connection():
                return False

        payload = {
            "anType": "edge",
            "key": f"{edge.source}-{edge.target}",
            "source": edge.source,
            "target": edge.target,
            "attrs": {
                "weight": edge.weight,
                "label": edge.label,
            },
        }

        try:
            resp = requests.post(
                f"{self.stream_url}/graph",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=1,
            )
            return resp.status_code in (200, 201)
        except Exception:
            return False

    def stream_batch(self, nodes: list[StreamNode], edges: list[StreamEdge]) -> dict[str, Any]:
        """Stream multiple nodes/edges in batch."""
        success = 0
        failed = 0

        for node in nodes:
            if self.stream_node(node):
                success += 1
            else:
                failed += 1

        for edge in edges:
            if self.stream_edge(edge):
                success += 1
            else:
                failed += 1

        return {
            "success": success,
            "failed": failed,
            "total": success + failed,
        }

    def clear_graph(self) -> bool:
        """Clear the Gephi graph."""
        try:
            resp = requests.delete(f"{self.stream_url}/graph", timeout=1)
            return resp.status_code == 200
        except Exception:
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get streaming statistics."""
        return {
            "connected": self.connected,
            "url": self.stream_url,
            "workspace": self.workspace,
            "stream_count": self.stream_count,
        }


class ActivationMonitor:
    """
    Monitors and streams model activations in real-time.

    Can be integrated with the LLM provider to watch
    activations as forensic queries are processed.
    """

    def __init__(self, streamer: GephiWebSocketStreamer | None = None, batch_size: int = 10):
        self.streamer = streamer or GephiWebSocketStreamer()
        self.batch_size = batch_size
        self.node_buffer: list[StreamNode] = []
        self.edge_buffer: list[StreamEdge] = []
        self.monitoring = False

    async def start_monitoring(self):
        """Start monitoring and streaming."""
        await self.streamer.connect()
        self.monitoring = True

    async def stop_monitoring(self):
        """Stop monitoring."""
        await self.streamer.disconnect()
        self.monitoring = False

    async def on_layer_activation(
        self, layer: int, activations: dict[str, float], concept: str = ""
    ):
        """Handle layer activation update."""
        if not self.monitoring:
            return

        for neur_id, act_value in activations.items():
            await self.streamer.stream_activation_update(
                layer=layer,
                neuron=int(neur_id) if isinstance(neur_id, int) else 0,
                activation=act_value,
                concept=concept,
            )

    async def on_triplet_extracted(self, triplets: list[dict], source_query: str = ""):
        """Handle triplet extraction update."""
        if not self.monitoring:
            return

        query_terms = source_query.lower().split()

        for i, triple in enumerate(triplets):
            subject = triple.get("subject", "")
            target = triple.get("target", "")

            subject_node = StreamNode(
                id=f"triplet_subj_{i}",
                label=subject,
                size=2.0,
                color="#00AAFF",
                attributes={
                    "type": "subject",
                    "query_match": any(t in subject.lower() for t in query_terms),
                },
            )

            target_node = StreamNode(
                id=f"triplet_obj_{i}",
                label=target,
                size=2.0,
                color="#00AAFF",
                attributes={
                    "type": "target",
                    "query_match": any(t in target.lower() for t in query_terms),
                },
            )

            edge = StreamEdge(
                source=f"triplet_subj_{i}",
                target=f"triplet_obj_{i}",
                weight=triple.get("confidence", 0.8),
                label=triple.get("relation", "related_to"),
            )

            await self.streamer.stream_node(subject_node)
            await self.streamer.stream_node(target_node)
            await self.streamer.stream_edge(edge)


async def stream_demo():
    """Demo of activation streaming."""
    streamer = GephiWebSocketStreamer()

    print("Attempting to connect to Gephi...")
    connected = await streamer.connect()

    if connected:
        print("Connected! Streaming demo nodes...")

        for i in range(5):
            node = StreamNode(
                id=f"demo_{i}",
                label=f"Neuron_{i}",
                size=1.0 + i * 0.5,
                color="#00FF00",
                attributes={"activation": 0.5 + i * 0.1},
            )
            await streamer.stream_node(node)

        await streamer.disconnect()
        print("Demo complete!")
    else:
        print("Could not connect to Gephi. Is it running with Graph Streaming plugin?")


def stream_activations_tool(activations: list[dict], connect: bool = False) -> dict[str, Any]:
    """MCP Tool: Stream activations to Gephi."""
    try:
        if not WEBSOCKETS_AVAILABLE:
            return {
                "status": "error",
                "error": "websockets not installed",
                "hint": "Run: pip install websockets",
            }

        async def run_stream():
            streamer = GephiWebSocketStreamer()

            if connect:
                await streamer.connect()

            for act in activations:
                layer = act.get("layer", 0)
                value = act.get("value", 0.1)
                concept = act.get("concept", "")

                await streamer.stream_activation_update(
                    layer=layer,
                    neuron=act.get("neuron", 0),
                    activation=value,
                    concept=concept,
                )

            if connect:
                await streamer.disconnect()

            return streamer.get_stats()

        stats = asyncio.run(run_stream())

        return {
            "status": "success",
            "streamed": stats["stream_count"],
            "connected": stats["connected"],
        }

    except Exception as e:
        logger.exception(f"Streaming failed: {e}")
        return {"status": "error", "error": str(e)}


def gephi_connection_tool() -> dict[str, Any]:
    """MCP Tool: Check Gephi connection status."""
    try:

        async def check():
            streamer = GephiWebSocketStreamer()
            await streamer.connect()
            stats = streamer.get_stats()
            await streamer.disconnect()
            return stats

        stats = asyncio.run(check())

        return {
            "status": "success",
            "connected": stats["connected"],
            "url": stats["gephi_url"],
            "workspace": stats["workspace"],
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
