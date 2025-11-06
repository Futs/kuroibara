"""
WebSocket manager for real-time progress updates.

This module provides WebSocket functionality for sending real-time progress
updates to connected clients.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""

    def __init__(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.id = str(uuid4())
        self.websocket = websocket
        self.user_id = user_id
        self.session_id = session_id
        self.subscribed_operations: Set[str] = set()
        self.subscribed_operation_types: Set[str] = set()
        self.is_active = True

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message to the WebSocket client.

        Returns:
            True if message was sent successfully
        """
        if not self.is_active:
            return False

        try:
            await self.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message to {self.id}: {e}")
            self.is_active = False
            return False

    def should_receive_event(self, event: Dict[str, Any]) -> bool:
        """Check if this connection should receive a specific event."""
        # Check user filtering
        if self.user_id and event.get("user_id") and event["user_id"] != self.user_id:
            return False

        # Check session filtering
        if (
            self.session_id
            and event.get("session_id")
            and event["session_id"] != self.session_id
        ):
            return False

        # Check operation subscription
        operation_id = event.get("operation_id")
        if (
            self.subscribed_operations
            and operation_id not in self.subscribed_operations
        ):
            return False

        # Check operation type subscription
        operation_type = event.get("operation_type")
        if (
            self.subscribed_operation_types
            and operation_type not in self.subscribed_operation_types
        ):
            return False

        return True

    def subscribe_to_operation(self, operation_id: str) -> None:
        """Subscribe to updates for a specific operation."""
        self.subscribed_operations.add(operation_id)

    def unsubscribe_from_operation(self, operation_id: str) -> None:
        """Unsubscribe from updates for a specific operation."""
        self.subscribed_operations.discard(operation_id)

    def subscribe_to_operation_type(self, operation_type: str) -> None:
        """Subscribe to updates for a specific operation type."""
        self.subscribed_operation_types.add(operation_type)

    def unsubscribe_from_operation_type(self, operation_type: str) -> None:
        """Unsubscribe from updates for a specific operation type."""
        self.subscribed_operation_types.discard(operation_type)


class WebSocketManager:
    """
    Manager for WebSocket connections and real-time progress updates.

    Features:
    - Connection management
    - Event broadcasting
    - Subscription filtering
    - Connection health monitoring
    """

    def __init__(self):
        self._connections: Dict[str, WebSocketConnection] = {}
        self._heartbeat_interval = 30  # seconds
        self._heartbeat_task: Optional[asyncio.Task] = None

        logger.info("WebSocketManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Accept a new WebSocket connection.

        Returns:
            Connection ID
        """
        await websocket.accept()

        connection = WebSocketConnection(websocket, user_id, session_id)
        self._connections[connection.id] = connection

        logger.info(
            f"WebSocket connected: {connection.id} (user: {user_id}, session: {session_id})"
        )

        # Send welcome message
        await connection.send_message(
            {
                "type": "connection_established",
                "connection_id": connection.id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Start heartbeat if this is the first connection
        if len(self._connections) == 1:
            await self._start_heartbeat()

        return connection.id

    async def disconnect(self, connection_id: str) -> None:
        """Disconnect a WebSocket connection."""
        if connection_id in self._connections:
            connection = self._connections[connection_id]
            connection.is_active = False
            del self._connections[connection_id]

            logger.info(f"WebSocket disconnected: {connection_id}")

            # Stop heartbeat if no connections remain
            if not self._connections:
                await self._stop_heartbeat()

    async def handle_message(self, connection_id: str, message: str) -> None:
        """Handle incoming WebSocket message."""
        connection = self._connections.get(connection_id)
        if not connection:
            return

        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "subscribe_operation":
                operation_id = data.get("operation_id")
                if operation_id:
                    connection.subscribe_to_operation(operation_id)
                    await connection.send_message(
                        {"type": "subscription_confirmed", "operation_id": operation_id}
                    )

            elif message_type == "unsubscribe_operation":
                operation_id = data.get("operation_id")
                if operation_id:
                    connection.unsubscribe_from_operation(operation_id)
                    await connection.send_message(
                        {
                            "type": "unsubscription_confirmed",
                            "operation_id": operation_id,
                        }
                    )

            elif message_type == "subscribe_operation_type":
                operation_type = data.get("operation_type")
                if operation_type:
                    connection.subscribe_to_operation_type(operation_type)
                    await connection.send_message(
                        {
                            "type": "subscription_confirmed",
                            "operation_type": operation_type,
                        }
                    )

            elif message_type == "unsubscribe_operation_type":
                operation_type = data.get("operation_type")
                if operation_type:
                    connection.unsubscribe_from_operation_type(operation_type)
                    await connection.send_message(
                        {
                            "type": "unsubscription_confirmed",
                            "operation_type": operation_type,
                        }
                    )

            elif message_type == "ping":
                await connection.send_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                )

            else:
                logger.warning(
                    f"Unknown message type from {connection_id}: {message_type}"
                )

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from WebSocket {connection_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message from {connection_id}: {e}")

    async def broadcast_event(self, event: Dict[str, Any]) -> int:
        """
        Broadcast an event to all relevant connections.

        Returns:
            Number of connections that received the event
        """
        if not self._connections:
            return 0

        sent_count = 0
        disconnected_connections = []

        for connection_id, connection in self._connections.items():
            if not connection.is_active:
                disconnected_connections.append(connection_id)
                continue

            if connection.should_receive_event(event):
                success = await connection.send_message(
                    {"type": "progress_event", "event": event}
                )

                if success:
                    sent_count += 1
                else:
                    disconnected_connections.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)

        return sent_count

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.

        Returns:
            True if message was sent successfully
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        return await connection.send_message(message)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send a message to all connections for a specific user.

        Returns:
            Number of connections that received the message
        """
        sent_count = 0

        for connection in self._connections.values():
            if connection.user_id == user_id and connection.is_active:
                success = await connection.send_message(message)
                if success:
                    sent_count += 1

        return sent_count

    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> int:
        """
        Send a message to all connections for a specific session.

        Returns:
            Number of connections that received the message
        """
        sent_count = 0

        for connection in self._connections.values():
            if connection.session_id == session_id and connection.is_active:
                success = await connection.send_message(message)
                if success:
                    sent_count += 1

        return sent_count

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len([c for c in self._connections.values() if c.is_active])

    def get_connections_for_user(self, user_id: str) -> List[WebSocketConnection]:
        """Get all active connections for a user."""
        return [
            c
            for c in self._connections.values()
            if c.user_id == user_id and c.is_active
        ]

    def get_connections_for_session(self, session_id: str) -> List[WebSocketConnection]:
        """Get all active connections for a session."""
        return [
            c
            for c in self._connections.values()
            if c.session_id == session_id and c.is_active
        ]

    async def _start_heartbeat(self) -> None:
        """Start the heartbeat task."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.debug("Started WebSocket heartbeat")

    async def _stop_heartbeat(self) -> None:
        """Stop the heartbeat task."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.debug("Stopped WebSocket heartbeat")

    async def _heartbeat_loop(self) -> None:
        """Heartbeat loop to check connection health."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                if not self._connections:
                    break

                # Send heartbeat to all connections
                disconnected = []
                for connection_id, connection in self._connections.items():
                    if connection.is_active:
                        success = await connection.send_message(
                            {
                                "type": "heartbeat",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                        if not success:
                            disconnected.append(connection_id)
                    else:
                        disconnected.append(connection_id)

                # Clean up disconnected connections
                for connection_id in disconnected:
                    await self.disconnect(connection_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket heartbeat: {e}")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
