"""
WebSocket service for real-time server updates.
"""

import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts.
    """

    def __init__(self):
        # Store active connections by server_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, server_id: int):
        """
        Accept a WebSocket connection for a specific server.

        Args:
            websocket: The WebSocket connection
            server_id: The server ID to subscribe to
        """
        await websocket.accept()
        if server_id not in self.active_connections:
            self.active_connections[server_id] = set()
        self.active_connections[server_id].add(websocket)
        print(f"✅ WebSocket connected for server {server_id} (total: {len(self.active_connections[server_id])})")

    def disconnect(self, websocket: WebSocket, server_id: int):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            server_id: The server ID to unsubscribe from
        """
        if server_id in self.active_connections:
            self.active_connections[server_id].discard(websocket)
            if not self.active_connections[server_id]:
                del self.active_connections[server_id]
        print(f"🔌 WebSocket disconnected for server {server_id}")

    async def broadcast_to_server(self, server_id: int, message: dict):
        """
        Broadcast a message to all connections subscribed to a server.

        Args:
            server_id: The server ID to broadcast to
            message: The message to broadcast
        """
        if server_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[server_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, server_id)

    async def broadcast_status_update(self, server_id: int, status: str, details: dict = None):
        """
        Broadcast a server status update.

        Args:
            server_id: The server ID
            status: The new status
            details: Optional additional details
        """
        message = {
            "type": "status_update",
            "server_id": server_id,
            "status": status,
            "details": details or {},
        }
        await self.broadcast_to_server(server_id, message)

    async def broadcast_download_progress(
        self, server_id: int, current: int, total: int, percentage: float
    ):
        """
        Broadcast Docker image download progress.

        Args:
            server_id: The server ID
            current: Current downloaded bytes
            total: Total bytes to download
            percentage: Download percentage
        """
        message = {
            "type": "download_progress",
            "server_id": server_id,
            "current": current,
            "total": total,
            "percentage": percentage,
        }
        await self.broadcast_to_server(server_id, message)

    async def broadcast_container_logs(self, server_id: int, logs: str):
        """
        Broadcast container logs.

        Args:
            server_id: The server ID
            logs: The log messages
        """
        message = {
            "type": "logs",
            "server_id": server_id,
            "logs": logs,
        }
        await self.broadcast_to_server(server_id, message)


# Global instance
manager = ConnectionManager()
