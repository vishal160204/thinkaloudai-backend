"""
ThinkAloud.ai — Voice Interview Endpoints
Start/end voice interview sessions via LiveKit.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import Session
from app.models.problem import Problem
from app.services.livekit_service import create_interview_room, generate_user_token, delete_room
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceStartResponse(BaseModel):
    livekit_url: str
    token: str
    room_name: str
    session_id: int


class VoiceEndRequest(BaseModel):
    transcript: str | None = None


@router.post("/start/{session_id}", response_model=VoiceStartResponse)
async def start_voice_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a voice interview for an existing session. Returns LiveKit token."""

    # Verify session belongs to user
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")

    # Get problem context for the agent
    result = await db.execute(select(Problem).where(Problem.id == session.problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    problem_context = (
        f"Title: {problem.title}\n"
        f"Difficulty: {problem.difficulty}\n"
        f"Description: {problem.description}\n"
        f"Constraints: {problem.constraints or 'None'}"
    )

    # Create LiveKit room
    room_info = await create_interview_room(session_id, problem_context)

    # Generate token for user
    token = generate_user_token(session_id, user.id, user.username)

    # Update session type
    session.session_type = "voice"
    await db.commit()

    logger.info(f"Voice session started: session={session_id}, user={user.id}")

    return VoiceStartResponse(
        livekit_url=settings.livekit_url,
        token=token,
        room_name=room_info["room_name"],
        session_id=session_id,
    )


@router.post("/end/{session_id}")
async def end_voice_session(
    session_id: int,
    data: VoiceEndRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """End a voice interview session. Optionally save transcript."""

    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete LiveKit room
    await delete_room(session_id)

    logger.info(f"Voice session ended: session={session_id}")

    return {"message": "Voice session ended", "session_id": session_id}
