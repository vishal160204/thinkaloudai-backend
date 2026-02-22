"""
ThinkAloud.ai — Problem Schemas
"""
from datetime import datetime

from pydantic import BaseModel


class ProblemListItem(BaseModel):
    id: int
    title: str
    slug: str
    difficulty: str
    category: str
    tags: list
    is_published: bool

    model_config = {"from_attributes": True}


class ProblemDetail(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    difficulty: str
    category: str
    constraints: str | None
    tags: list
    hints: list
    starter_code: dict
    test_cases: list  # Only non-hidden ones will be filtered in the endpoint
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}
