"""
ThinkAloud.ai — Stats Schemas
"""
from datetime import date

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_sessions: int
    total_problems_attempted: int
    total_problems_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    current_streak: int
    longest_streak: int
    avg_score: float


class StreakDay(BaseModel):
    date: date
    activity_count: int

    model_config = {"from_attributes": True}


class ProgressItem(BaseModel):
    problem_id: int
    problem_title: str
    difficulty: str
    attempts: int
    best_score: int
    is_solved: bool

    model_config = {"from_attributes": True}
