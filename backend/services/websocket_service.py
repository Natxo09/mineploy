"""
WebSocket service for real-time server updates.

Supports multiple channels per server:
- status_updates: Server status changes
- minecraft_logs: Real-time Minecraft server logs
- container_logs: Real-time Docker container logs
"""

import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts.
    Supports multiple channels per server for different types of data streams.
    """

    def __init__(self):
        # Store active connections by (server_id, channel)
        # Key: (server_id, channel), Value: Set[WebSocket]
        self.active_connections: Dict[tuple[int, str], Set[WebSocket]] = {}

        # Store active streaming tasks
        # Key: (server_id, channel), Value: asyncio.Task
        self.streaming_tasks: Dict[tuple[int, str], asyncio.Task] = {}

        # Store container_ids for streaming
        # Key: server_id, Value: container_id
        self.server_containers: Dict[int, str] = {}

    async def connect(self, websocket: WebSocket, server_id: int, channel: str = "default"):
        """
        Accept a WebSocket connection for a specific server and channel.

        Args:
            websocket: The WebSocket connection
            server_id: The server ID to subscribe to
            channel: The channel to subscribe to (default, minecraft_logs, container_logs)
        """
        await websocket.accept()

        key = (server_id, channel)
        if key not in self.active_connections:
            self.active_connections[key] = set()

        self.active_connections[key].add(websocket)
        print(f"✅ WebSocket connected for server {server_id}, channel '{channel}' (total: {len(self.active_connections[key])})")

    def disconnect(self, websocket: WebSocket, server_id: int, channel: str = "default"):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            server_id: The server ID to unsubscribe from
            channel: The channel to unsubscribe from
        """
        key = (server_id, channel)
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)

            # If no more connections for this channel, stop streaming task
            if not self.active_connections[key]:
                del self.active_connections[key]
                self._stop_streaming_task(server_id, channel)

        print(f"🔌 WebSocket disconnected for server {server_id}, channel '{channel}'")

    def get_connection_count(self, server_id: int, channel: str = "default") -> int:
        """
        Get the number of active connections for a server and channel.

        Args:
            server_id: The server ID
            channel: The channel

        Returns:
            Number of active connections
        """
        key = (server_id, channel)
        return len(self.active_connections.get(key, set()))

    async def broadcast_to_server(
        self,
        server_id: int,
        message: dict,
        channel: str = "default"
    ):
        """
        Broadcast a message to all connections subscribed to a server channel.

        Args:
            server_id: The server ID to broadcast to
            message: The message to broadcast
            channel: The channel to broadcast to
        """
        key = (server_id, channel)
        if key not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[key]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, server_id, channel)

    async def broadcast_status_update(self, server_id: int, status: str, details: dict = None):
        """
        Broadcast a server status update to the default channel.

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
        await self.broadcast_to_server(server_id, message, channel="default")

    async def broadcast_download_progress(
        self, server_id: int, current: int, total: int, percentage: float
    ):
        """
        Broadcast Docker image download progress to the default channel.

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
        await self.broadcast_to_server(server_id, message, channel="default")

    async def broadcast_container_logs(self, server_id: int, logs: str):
        """
        Broadcast container logs to the default channel (legacy method).

        Args:
            server_id: The server ID
            logs: The log messages
        """
        message = {
            "type": "logs",
            "server_id": server_id,
            "logs": logs,
        }
        await self.broadcast_to_server(server_id, message, channel="default")

    async def broadcast_log_line(
        self,
        server_id: int,
        line: str,
        channel: str = "container_logs"
    ):
        """
        Broadcast a single log line to subscribers.

        Args:
            server_id: The server ID
            line: The log line
            channel: The channel (minecraft_logs or container_logs)
        """
        message = {
            "type": "log_line",
            "server_id": server_id,
            "line": line,
            "channel": channel,
        }
        await self.broadcast_to_server(server_id, message, channel=channel)

    def register_server_container(self, server_id: int, container_id: str):
        """
        Register a server's container ID for log streaming.

        Args:
            server_id: The server ID
            container_id: The container ID
        """
        self.server_containers[server_id] = container_id

    def unregister_server_container(self, server_id: int):
        """
        Unregister a server's container ID.

        Args:
            server_id: The server ID
        """
        if server_id in self.server_containers:
            del self.server_containers[server_id]

    def _stop_streaming_task(self, server_id: int, channel: str):
        """
        Stop a streaming task for a server and channel.

        Args:
            server_id: The server ID
            channel: The channel
        """
        key = (server_id, channel)
        if key in self.streaming_tasks:
            task = self.streaming_tasks[key]
            task.cancel()
            del self.streaming_tasks[key]
            print(f"🛑 Stopped streaming task for server {server_id}, channel '{channel}'")

    async def start_log_streaming(
        self,
        server_id: int,
        container_id: str,
        channel: str,
        log_type: str = "container"
    ):
        """
        Start streaming logs for a server.

        Args:
            server_id: The server ID
            container_id: The container ID
            channel: The channel to stream to
            log_type: Type of logs ('container' or 'minecraft')
        """
        from services.docker_service import docker_service
        from services.minecraft_logs_service import minecraft_logs_service

        key = (server_id, channel)

        # Don't start if already running
        if key in self.streaming_tasks:
            return

        async def stream_logs():
            """Background task to stream logs."""
            try:
                print(f"📡 Starting log stream for server {server_id}, channel '{channel}', type '{log_type}'")

                if log_type == "minecraft":
                    # Stream from /data/logs/latest.log
                    file_path = "/data/logs/latest.log"
                    command = ['sh', '-c', f'tail -f -n 50 {file_path} 2>/dev/null || echo "Waiting for logs..."']
                else:
                    # Stream from Docker logs
                    # Note: Docker logs API doesn't support true streaming with aiodocker
                    # We'll poll every 2 seconds for new logs
                    last_timestamp = None

                    while True:
                        try:
                            # Get recent logs
                            logs = await docker_service.get_container_logs(
                                container_id,
                                tail=50
                            )

                            # Filter and send logs
                            if log_type == "container":
                                logs = minecraft_logs_service.filter_docker_logs(logs)

                            for line in logs.split('\n'):
                                if line.strip():
                                    await self.broadcast_log_line(server_id, line, channel)

                            await asyncio.sleep(2)

                        except Exception as e:
                            print(f"⚠️  Error streaming Docker logs: {e}")
                            await asyncio.sleep(5)

                    return  # Exit for Docker logs (polling-based)

                # For Minecraft logs with exec (tail -f)
                await docker_service.connect()
                container = docker_service.docker.containers.container(container_id)

                # Create exec instance for tail -f
                exec_instance = await container.exec(command)
                stream = exec_instance.start(stream=True)

                # Stream lines
                async for chunk in stream:
                    if isinstance(chunk, bytes):
                        chunk = chunk.decode('utf-8', errors='ignore')

                    for line in chunk.split('\n'):
                        if line.strip():
                            await self.broadcast_log_line(server_id, line, channel)

            except asyncio.CancelledError:
                print(f"🛑 Log streaming cancelled for server {server_id}, channel '{channel}'")
                raise
            except Exception as e:
                print(f"❌ Error in log streaming for server {server_id}: {e}")
            finally:
                # Clean up
                if key in self.streaming_tasks:
                    del self.streaming_tasks[key]

        # Create and store the task
        task = asyncio.create_task(stream_logs())
        self.streaming_tasks[key] = task

    def stop_log_streaming(self, server_id: int, channel: str):
        """
        Stop log streaming for a server and channel.

        Args:
            server_id: The server ID
            channel: The channel
        """
        self._stop_streaming_task(server_id, channel)


# Global instance
manager = ConnectionManager()
