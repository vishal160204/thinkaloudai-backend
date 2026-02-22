"""
ThinkAloud.ai — Stats & Progress Endpoints
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import Session
from app.models.problem import Problem
from app.models.feedback import Feedback
from app.models.user_progress import UserProgress
from app.models.streak import Streak
from app.schemas.stats import DashboardStats, StreakDay, ProgressItem

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard stats for the current user."""

    # Total sessions
    result = await db.execute(
        select(func.count()).select_from(Session).where(Session.user_id == user.id)
    )
    total_sessions = result.scalar()

    # Problems attempted & solved
    result = await db.execute(
        select(func.count()).select_from(UserProgress).where(UserProgress.user_id == user.id)
    )
    total_attempted = result.scalar()

    result = await db.execute(
        select(func.count())
        .select_from(UserProgress)
        .where(UserProgress.user_id == user.id, UserProgress.is_solved == True)
    )
    total_solved = result.scalar()

    # Solved by difficulty
    easy = medium = hard = 0
    result = await db.execute(
        select(Problem.difficulty, func.count())
        .join(UserProgress, UserProgress.problem_id == Problem.id)
        .where(UserProgress.user_id == user.id, UserProgress.is_solved == True)
        .group_by(Problem.difficulty)
    )
    for difficulty, count in result.all():
        if difficulty == "easy":
            easy = count
        elif difficulty == "medium":
            medium = count
        elif difficulty == "hard":
            hard = count

    # Streaks
    result = await db.execute(
        select(Streak.date)
        .where(Streak.user_id == user.id)
        .order_by(Streak.date.desc())
    )
    dates = [row[0] for row in result.all()]

    current_streak = 0
    longest_streak = 0
    if dates:
        # Calculate current streak
        today = date.today()
        check_date = today
        temp_streak = 0
        for d in dates:
            if d == check_date:
                temp_streak += 1
                check_date -= timedelta(days=1)
            elif d == check_date - timedelta(days=1):
                # Allow for yesterday start
                check_date = d
                temp_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        current_streak = temp_streak

        # Calculate longest streak
        temp = 1
        for i in range(1, len(dates)):
            if dates[i - 1] - dates[i] == timedelta(days=1):
                temp += 1
            else:
                longest_streak = max(longest_streak, temp)
                temp = 1
        longest_streak = max(longest_streak, temp)

    # Average score
    result = await db.execute(
        select(func.avg(Feedback.overall_score))
        .join(Session, Session.id == Feedback.session_id)
        .where(Session.user_id == user.id)
    )
    avg_score = result.scalar() or 0.0

    return DashboardStats(
        total_sessions=total_sessions,
        total_problems_attempted=total_attempted,
        total_problems_solved=total_solved,
        easy_solved=easy,
        medium_solved=medium,
        hard_solved=hard,
        current_streak=current_streak,
        longest_streak=longest_streak,
        avg_score=round(avg_score, 1),
    )


@router.get("/streaks", response_model=list[StreakDay])
async def get_streaks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get streak data for the last 365 days (for heatmap)."""
    cutoff = date.today() - timedelta(days=365)
    result = await db.execute(
        select(Streak)
        .where(Streak.user_id == user.id, Streak.date >= cutoff)
        .order_by(Streak.date)
    )
    return result.scalars().all()


@router.get("/progress", response_model=list[ProgressItem])
async def get_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get per-problem progress for the current user."""
    result = await db.execute(
        select(
            UserProgress.problem_id,
            Problem.title.label("problem_title"),
            Problem.difficulty,
            UserProgress.attempts,
            UserProgress.best_score,
            UserProgress.is_solved,
        )
        .join(Problem, Problem.id == UserProgress.problem_id)
        .where(UserProgress.user_id == user.id)
        .order_by(UserProgress.last_attempt_at.desc())
    )
    return [
        ProgressItem(
            problem_id=row.problem_id,
            problem_title=row.problem_title,
            difficulty=row.difficulty,
            attempts=row.attempts,
            best_score=row.best_score,
            is_solved=row.is_solved,
        )
        for row in result.all()
    ]
