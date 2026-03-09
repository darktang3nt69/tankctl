"""
WebSocket broadcasting for frontend live updates.

Receives domain events from the existing event publisher and fans them out to
connected frontend clients over a single WebSocket endpoint.
"""

import asyncio
from typing import Any

from fastapi import WebSocket

from src.domain.event import Event
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """Manage connected WebSocket clients and broadcast live events."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[dict[str, Any]] | None = None
        self._broadcast_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Initialize the broadcast queue and worker task."""
        if self._broadcast_task and not self._broadcast_task.done():
            return

        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue(maxsize=1000)
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("websocket_manager_started")

    async def stop(self) -> None:
        """Stop the worker and close active client connections."""
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
            self._broadcast_task = None

        for websocket in list(self._connections):
            try:
                await websocket.close()
            except Exception:
                pass

        self._connections.clear()
        self._queue = None
        self._loop = None
        logger.info("websocket_manager_stopped")

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new client connection."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("websocket_client_connected", connections=len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a client connection if present."""
        if websocket in self._connections:
            self._connections.remove(websocket)
            logger.info("websocket_client_disconnected", connections=len(self._connections))

    def enqueue_event(self, event: Event) -> None:
        """Queue a domain event for async broadcast from any thread."""
        if not self._loop or not self._queue:
            return

        payload = self._serialize_event(event)

        def _enqueue() -> None:
            if not self._queue:
                return
            if self._queue.full():
                logger.warning(
                    "websocket_event_dropped",
                    event=event.event,
                    device_id=event.device_id,
                )
                return
            self._queue.put_nowait(payload)

        self._loop.call_soon_threadsafe(_enqueue)

    async def _broadcast_loop(self) -> None:
        """Read queued events and fan them out to all clients."""
        while True:
            if not self._queue:
                await asyncio.sleep(0.1)
                continue

            payload = await self._queue.get()
            if self._connections:
                await self._broadcast(payload)

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        stale_connections: list[WebSocket] = []

        for websocket in list(self._connections):
            try:
                await websocket.send_json(payload)
            except Exception as exc:
                logger.warning("websocket_broadcast_failed", error=str(exc))
                stale_connections.append(websocket)

        for websocket in stale_connections:
            await self.disconnect(websocket)

    def _serialize_event(self, event: Event) -> dict[str, Any]:
        return {
            "event": event.event,
            "device_id": event.device_id,
            "timestamp": event.timestamp,
            "metadata": event.metadata or {},
        }


websocket_manager = WebSocketManager()