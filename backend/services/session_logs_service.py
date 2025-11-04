"""
Service for managing server session logs.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.server import Server


class SessionLogsService:
    """Manage session logs with a circular buffer (max 5000 lines)."""

    MAX_LINES = 5000

    @staticmethod
    async def append_log_line(
        server_id: int,
        log_line: str,
        db: AsyncSession
    ) -> None:
        """
        Append a log line to the server's current session logs.

        Implements a circular buffer: when reaching MAX_LINES,
        the oldest line is removed to make room for the new one.

        Args:
            server_id: Server ID
            log_line: Log line to append
            db: Database session
        """
        # Get server
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()

        if not server:
            return

        # Get current logs
        current_logs = server.current_session_logs or ""

        # Split into lines
        lines = current_logs.split("\n") if current_logs else []

        # Append new line
        lines.append(log_line.strip())

        # Keep only last MAX_LINES (circular buffer)
        if len(lines) > SessionLogsService.MAX_LINES:
            lines = lines[-SessionLogsService.MAX_LINES:]

        # Update server
        server.current_session_logs = "\n".join(lines)
        await db.commit()

    @staticmethod
    async def get_session_logs(
        server_id: int,
        db: AsyncSession,
        tail: int | None = None
    ) -> str:
        """
        Get session logs for a server.

        Args:
            server_id: Server ID
            db: Database session
            tail: Number of lines to return from the end (None = all)

        Returns:
            Session logs as string
        """
        # Get server
        result = await db.execute(select(Server).where(Server.id == server_id))
        server = result.scalar_one_or_none()

        if not server or not server.current_session_logs:
            return ""

        # Apply tail if requested
        if tail:
            lines = server.current_session_logs.split("\n")
            lines = lines[-tail:]
            return "\n".join(lines)

        return server.current_session_logs


# Global instance
session_logs_service = SessionLogsService()
