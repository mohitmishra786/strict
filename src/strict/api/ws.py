from typing import Any

from fastapi import WebSocket
from strict.observability.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept connection and add to active list."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New connection. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove connection from active list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"Connection closed. Total active: {len(self.active_connections)}"
            )
        else:
            logger.warning("Attempted to disconnect an inactive websocket")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to a specific connection."""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Send message to all active connections."""
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_json(self, data: dict[str, Any], websocket: WebSocket):
        """Send JSON data to a specific connection."""
        await websocket.send_json(data)


manager = ConnectionManager()
