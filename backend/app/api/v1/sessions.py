"""
ThinkAloud.ai — Sessions Endpoints
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import Session
from app.models.submission import Submission
from app.models.problem import Problem
from app.models.user_progress import UserProgress
from app.models.streak import Streak
from app.schemas.session import (
    StartSessionRequest, SubmitCodeRequest,
    SessionResponse, SubmissionResponse, SessionDetailResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def start_session(
    data: StartSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new practice/interview session for a problem."""
    # Verify problem exists
    result = await db.execute(select(Problem).where(Problem.id == data.problem_id))
    problem = result.scalar_one_or_none()
    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")

    session = Session(
        user_id=user.id,
        problem_id=data.problem_id,
        session_type=data.session_type,
        language=data.language,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all sessions for the current user, most recent first."""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.started_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session detail with submissions and feedback."""
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id, Session.user_id == user.id)
        .options(selectinload(Session.submissions), selectinload(Session.feedback))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/submit", response_model=SubmissionResponse)
async def submit_code(
    session_id: int,
    data: SubmitCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit code, execute against test cases, and save results."""
    # Verify session
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")

    # Get problem for test cases
    result = await db.execute(select(Problem).where(Problem.id == session.problem_id))
    problem = result.scalar_one_or_none()

    # Run tests if problem has test cases
    test_results_data = None
    execution_data = None
    tests_passed = 0
    tests_total = 0

    if problem and problem.test_cases:
        from app.services.test_runner import run_tests

        run_result = await run_tests(data.code, data.language, problem.test_cases)
        test_results_data = run_result["test_results"]
        execution_data = run_result["execution_result"]
        tests_passed = run_result["tests_passed"]
        tests_total = run_result["tests_total"]
    else:
        # No test cases — just run the code
        from app.services.code_runner import run_code

        execution_data = await run_code(data.code, data.language)

    # Save submission
    submission = Submission(
        session_id=session_id,
        code=data.code,
        language=data.language,
        execution_result=execution_data,
        test_results=test_results_data,
        tests_passed=tests_passed,
        tests_total=tests_total,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return submission



@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a session as completed. Updates duration, progress, and streak."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")

    now = datetime.now(timezone.utc)
    session.status = "completed"
    session.completed_at = now
    session.duration_seconds = int((now - session.started_at).total_seconds())

    # Update user progress
    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user.id,
            UserProgress.problem_id == session.problem_id,
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = UserProgress(user_id=user.id, problem_id=session.problem_id)
        db.add(progress)
    progress.attempts += 1
    progress.last_attempt_at = now

    # Update streak
    today = now.date()
    result = await db.execute(
        select(Streak).where(Streak.user_id == user.id, Streak.date == today)
    )
    streak = result.scalar_one_or_none()
    if streak:
        streak.activity_count += 1
    else:
        db.add(Streak(user_id=user.id, date=today, activity_count=1))

    await db.commit()
    await db.refresh(session)
    return session
