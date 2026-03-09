"""Live update WebSocket endpoint."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.infrastructure.events.websocket_manager import websocket_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["live"])


@router.websocket("/ws")
async def websocket_live_updates(websocket: WebSocket) -> None:
    """Single frontend WebSocket endpoint for live backend events."""
    await websocket_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("websocket_client_error", error=str(exc))
        await websocket_manager.disconnect(websocket)