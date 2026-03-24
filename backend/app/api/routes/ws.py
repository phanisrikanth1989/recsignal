"""WebSocket endpoint for real-time metric streaming."""

from __future__ import annotations

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    topics: str = Query(default="dashboard,hosts,alerts"),
):
    """
    WebSocket endpoint for real-time updates.

    Connect with topics as comma-separated query param:
      ws://host/ws?topics=dashboard,hosts,alerts
      ws://host/ws?topics=host:3
    """
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    await manager.connect(websocket, topic_list)
    try:
        while True:
            # Keep connection alive; client can send pings or subscribe to more topics
            data = await websocket.receive_text()
            # Handle dynamic subscription changes
            if data.startswith("subscribe:"):
                new_topics = [t.strip() for t in data[10:].split(",") if t.strip()]
                for topic in new_topics:
                    if topic not in manager._subscriptions:
                        manager._subscriptions[topic] = set()
                    manager._subscriptions[topic].add(websocket)
                    logger.info("Client subscribed to: %s", topic)
            elif data.startswith("unsubscribe:"):
                old_topics = [t.strip() for t in data[12:].split(",") if t.strip()]
                for topic in old_topics:
                    if topic in manager._subscriptions:
                        manager._subscriptions[topic].discard(websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
