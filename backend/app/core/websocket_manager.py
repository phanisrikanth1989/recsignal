"""WebSocket connection manager for real-time metric broadcasting."""

from __future__ import annotations

import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates to subscribers."""

    def __init__(self):
        # topic -> set of websockets
        # Topics: "dashboard", "hosts", "host:{id}", "alerts"
        self._subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, topics: list[str]):
        await websocket.accept()
        for topic in topics:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = set()
            self._subscriptions[topic].add(websocket)
        logger.info("WebSocket connected, subscribed to: %s", topics)

    def disconnect(self, websocket: WebSocket):
        for topic_subs in self._subscriptions.values():
            topic_subs.discard(websocket)
        logger.info("WebSocket disconnected")

    async def broadcast(self, topic: str, data: dict):
        """Send data to all connections subscribed to the given topic."""
        subscribers = self._subscriptions.get(topic, set())
        if not subscribers:
            return
        message = json.dumps({"topic": topic, "data": data})
        dead: list[WebSocket] = []
        for ws in subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        seen: set[int] = set()
        count = 0
        for subs in self._subscriptions.values():
            for ws in subs:
                ws_id = id(ws)
                if ws_id not in seen:
                    seen.add(ws_id)
                    count += 1
        return count


# Singleton instance
manager = ConnectionManager()
