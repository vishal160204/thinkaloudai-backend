"""
ThinkAloud.ai — AI Feedback Endpoint
Generate AI-powered code analysis using vLLM on MI300X.
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
from app.models.submission import Submission
from app.models.feedback import Feedback
from app.services.llm_service import generate_code_feedback, generate_hint

logger = logging.getLogger(__name__)
router = APIRouter()


class HintRequest(BaseModel):
    code: str
    language: str


@router.post("/sessions/{session_id}/feedback")
async def get_ai_feedback(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI feedback for the latest submission in a session."""

    # Get session
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get latest submission
    result = await db.execute(
        select(Submission)
        .where(Submission.session_id == session_id)
        .order_by(Submission.submitted_at.desc())
        .limit(1)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=400, detail="No submission found")

    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == session.problem_id))
    problem = result.scalar_one_or_none()

    # Generate feedback
    feedback_data = await generate_code_feedback(
        code=submission.code,
        language=submission.language,
        problem_title=problem.title if problem else "Unknown",
        problem_description=problem.description if problem else "",
        tests_passed=submission.tests_passed or 0,
        tests_total=submission.tests_total or 0,
    )

    # Save feedback to DB
    feedback = Feedback(
        session_id=session_id,
        overall_score=feedback_data.get("overall_score", 0),
        strengths=feedback_data.get("strengths", []),
        weaknesses=feedback_data.get("weaknesses", []),
        suggestions=feedback_data.get("suggestions", []),
        summary=feedback_data.get("summary", ""),
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return {
        **feedback_data,
        "feedback_id": feedback.id,
        "session_id": session_id,
    }


@router.post("/problems/{problem_id}/hint")
async def get_hint(
    problem_id: int,
    data: HintRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an AI-generated hint for a problem. Never reveals the solution."""

    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    hint = await generate_hint(
        problem_title=problem.title,
        problem_description=problem.description,
        user_code=data.code,
        language=data.language,
    )

    return {"hint": hint, "problem_id": problem_id}
