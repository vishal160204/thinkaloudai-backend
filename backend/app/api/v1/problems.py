"""
ThinkAloud.ai — Problems Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_db
from app.models.problem import Problem
from app.schemas.problem import ProblemListItem, ProblemDetail

router = APIRouter()


@router.get("/", response_model=list[ProblemListItem])
async def list_problems(
    difficulty: str | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all published problems with optional filters and pagination."""
    query = select(Problem).where(Problem.is_published == True)

    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
    if category:
        query = query.where(Problem.category == category)

    query = query.order_by(Problem.id).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{slug}", response_model=ProblemDetail)
async def get_problem(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a single problem by slug. Hides hidden test cases."""
    result = await db.execute(select(Problem).where(Problem.slug == slug))
    problem = result.scalar_one_or_none()

    if not problem or not problem.is_published:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Filter out hidden test cases
    visible_tests = [t for t in problem.test_cases if not t.get("is_hidden", False)]

    return ProblemDetail(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        description=problem.description,
        difficulty=problem.difficulty,
        category=problem.category,
        constraints=problem.constraints,
        tags=problem.tags,
        hints=problem.hints,
        starter_code=problem.starter_code,
        test_cases=visible_tests,
        is_published=problem.is_published,
        created_at=problem.created_at,
    )
