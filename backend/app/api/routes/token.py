"""
Issues short-lived LiveKit access tokens for frontend clients.
Called once per chat session before the WebRTC connection is established.
"""
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import APIRouter, HTTPException, status
from livekit.api import AccessToken, VideoGrants

logger = logging.getLogger(__name__)
router = APIRouter(tags=["livekit"])

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
ROOM_NAME = "museum-assistant"


@router.get("/livekit/token", summary="Issue a LiveKit room token for the chat client")
async def get_livekit_token(visitor_id: str = "visitor", locale: str = "ar") -> dict:
    """
    Returns a signed JWT that lets the frontend join the LiveKit room.
    Each visitor gets a unique identity based on visitor_id + timestamp.
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LiveKit credentials not configured.",
        )

    identity = f"{visitor_id}-{int(time.time())}"
    room_name = f"museum-assistant-{identity}"
    import json

    try:
        token = (
            AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(f"Museum Visitor {identity}")
            .with_metadata(json.dumps({"locale": locale}))
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .to_jwt()
        )
    except Exception as exc:
        logger.exception("Token generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access token.",
        )

    logger.info("Token issued for identity: %s, room: %s", identity, room_name)
    return {"token": token, "room": room_name}
