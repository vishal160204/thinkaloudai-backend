"""
ThinkAloud.ai — LiveKit Service
Creates rooms and generates access tokens for voice interview sessions.
All config from settings — zero hardcoded values.
"""
import logging
from livekit import api

from app.config import settings

logger = logging.getLogger(__name__)


async def create_interview_room(session_id: int, problem_context: str) -> dict:
    """
    Create a LiveKit room for a voice interview session.
    Problem context is passed as room metadata so the agent can access it.
    """
    room_service = api.RoomService(
        settings.livekit_url,
        settings.livekit_api_key,
        settings.livekit_api_secret,
    )

    room = await room_service.create_room(
        api.CreateRoomRequest(
            name=f"interview-{session_id}",
            metadata=problem_context,
            empty_timeout=300,       # Close after 5 min if empty
            max_participants=2,      # User + Agent
        )
    )

    logger.info(f"Created LiveKit room: interview-{session_id}")
    return {
        "room_name": room.name,
        "room_sid": room.sid,
    }


def generate_user_token(session_id: int, user_id: int, username: str) -> str:
    """Generate a JWT token for the user to join the LiveKit room."""
    token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
    token.with_identity(f"user-{user_id}")
    token.with_name(username)
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=f"interview-{session_id}",
        )
    )
    return token.to_jwt()


async def delete_room(session_id: int) -> None:
    """Delete a LiveKit room when interview ends."""
    try:
        room_service = api.RoomService(
            settings.livekit_url,
            settings.livekit_api_key,
            settings.livekit_api_secret,
        )
        await room_service.delete_room(
            api.DeleteRoomRequest(room=f"interview-{session_id}")
        )
        logger.info(f"Deleted LiveKit room: interview-{session_id}")
    except Exception as e:
        logger.warning(f"Failed to delete room interview-{session_id}: {e}")
