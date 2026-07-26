"""
Native FastAPI WebSocket Endpoints

Provides real-time streaming updates for:
- Live evaluation progress & per-question score metrics
- Real-time job status updates
"""

from __future__ import annotations

import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.redis import redis_client

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/evaluations/{job_id}")
async def evaluation_progress_websocket(websocket: WebSocket, job_id: str) -> None:
    """
    Native WebSocket endpoint for live evaluation progress.

    Subscribes to Redis pub/sub channel `eval:{job_id}` and pushes JSON messages
    directly to the connected frontend client.
    """
    await websocket.accept()
    logger.info("websocket_client_connected", job_id=job_id)

    channel_name = f"eval:{job_id}"
    pubsub = None

    try:
        if redis_client._client:
            pubsub = redis_client._client.pubsub()
            await pubsub.subscribe(channel_name)

            while True:
                # Read message with non-blocking timeout
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data_str = message.get("data")
                    if isinstance(data_str, bytes):
                        data_str = data_str.decode("utf-8")
                    await websocket.send_text(data_str)

                    # Close cleanly when completed
                    try:
                        parsed = json.loads(data_str)
                        if parsed.get("type") in ["completed", "failed", "cancelled"]:
                            await asyncio.sleep(0.5)
                            break
                    except Exception:
                        pass

                await asyncio.sleep(0.1)

        else:
            # Fallback heartbeat if Redis pub/sub is not connected
            await websocket.send_json({
                "type": "progress",
                "evaluation_id": job_id,
                "status": "running",
                "message": "WebSocket connected (direct mode)",
            })
            await asyncio.sleep(2.0)

    except WebSocketDisconnect:
        logger.info("websocket_client_disconnected", job_id=job_id)
    except Exception as err:
        logger.error("websocket_error", job_id=job_id, error=str(err))
    finally:
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
        try:
            await websocket.close()
        except Exception:
            pass
