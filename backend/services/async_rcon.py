"""
Async RCON client implementation without signal handlers.
Based on the Source RCON Protocol specification.
"""

import asyncio
import struct
from typing import Optional


class RconError(Exception):
    """RCON communication error."""
    pass


class AsyncRconClient:
    """
    Asynchronous RCON client for Minecraft servers.
    Implements the Source RCON Protocol without using signal handlers.
    """

    # Packet types
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0

    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0):
        """
        Initialize RCON client.

        Args:
            host: Server hostname or IP
            port: RCON port
            password: RCON password
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0
        self._authenticated = False

    def _get_request_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _encode_packet(self, request_id: int, packet_type: int, payload: str) -> bytes:
        """
        Encode RCON packet.

        Packet format:
        - Size (4 bytes, little-endian int32)
        - Request ID (4 bytes, little-endian int32)
        - Type (4 bytes, little-endian int32)
        - Payload (null-terminated ASCII string)
        - Empty string (null terminator)
        """
        payload_bytes = payload.encode('utf-8') + b'\x00\x00'
        packet_size = 4 + 4 + len(payload_bytes)  # ID + Type + Payload

        packet = struct.pack('<i', packet_size)  # Size
        packet += struct.pack('<i', request_id)  # Request ID
        packet += struct.pack('<i', packet_type)  # Type
        packet += payload_bytes  # Payload with null terminators

        return packet

    def _decode_packet(self, data: bytes) -> tuple[int, int, str]:
        """
        Decode RCON packet.

        Returns:
            Tuple of (request_id, packet_type, payload)
        """
        if len(data) < 12:
            raise RconError("Packet too short")

        size = struct.unpack('<i', data[0:4])[0]
        request_id = struct.unpack('<i', data[4:8])[0]
        packet_type = struct.unpack('<i', data[8:12])[0]

        # Payload is from byte 12 to end, minus 2 null terminators
        payload_bytes = data[12:12 + size - 8]
        payload = payload_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')

        return request_id, packet_type, payload

    async def connect(self) -> None:
        """
        Connect to RCON server and authenticate.

        Raises:
            RconError: If connection or authentication fails
        """
        try:
            # Open connection
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout
            )

            # Send authentication packet
            auth_id = self._get_request_id()
            auth_packet = self._encode_packet(
                auth_id,
                self.SERVERDATA_AUTH,
                self.password
            )
            self.writer.write(auth_packet)
            await self.writer.drain()

            # Read authentication response
            response_data = await asyncio.wait_for(
                self.reader.read(4096),
                timeout=self.timeout
            )

            if not response_data:
                raise RconError("No authentication response from server")

            response_id, response_type, _ = self._decode_packet(response_data)

            # Check authentication result
            if response_id == -1 or response_id != auth_id:
                raise RconError("Authentication failed - invalid password")

            self._authenticated = True

        except asyncio.TimeoutError:
            raise RconError(f"Connection timeout after {self.timeout}s")
        except ConnectionRefusedError:
            raise RconError(f"Connection refused to {self.host}:{self.port}")
        except Exception as e:
            raise RconError(f"Connection error: {str(e)}")

    async def send_command(self, command: str) -> str:
        """
        Send command to server and get response.

        Args:
            command: Command to execute

        Returns:
            Command response from server

        Raises:
            RconError: If command execution fails
        """
        if not self._authenticated or not self.writer or not self.reader:
            raise RconError("Not connected or authenticated")

        try:
            # Send command packet
            cmd_id = self._get_request_id()
            cmd_packet = self._encode_packet(
                cmd_id,
                self.SERVERDATA_EXECCOMMAND,
                command
            )
            self.writer.write(cmd_packet)
            await self.writer.drain()

            # Read response
            response_data = await asyncio.wait_for(
                self.reader.read(4096),
                timeout=self.timeout
            )

            if not response_data:
                raise RconError("No response from server")

            _, _, payload = self._decode_packet(response_data)
            return payload

        except asyncio.TimeoutError:
            raise RconError(f"Command timeout after {self.timeout}s")
        except Exception as e:
            raise RconError(f"Command error: {str(e)}")

    async def close(self) -> None:
        """Close connection."""
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass
            self.writer = None
            self.reader = None
            self._authenticated = False

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
