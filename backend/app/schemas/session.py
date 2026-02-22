"""
ThinkAloud.ai — Session Schemas
"""
from datetime import datetime

from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    problem_id: int
    session_type: str = "practice"  # practice | interview | voice
    language: str = "python"


class SubmitCodeRequest(BaseModel):
    code: str
    language: str = "python"


class SessionResponse(BaseModel):
    id: int
    problem_id: int
    session_type: str
    status: str
    language: str
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    id: int
    session_id: int
    code: str
    language: str
    tests_passed: int
    tests_total: int
    execution_result: dict | None
    test_results: list | None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class FeedbackResponse(BaseModel):
    overall_score: int
    approach_score: int
    code_quality_score: int
    communication_score: int
    strengths: list
    weaknesses: list
    suggestions: list
    summary: str | None

    model_config = {"from_attributes": True}


class SessionDetailResponse(SessionResponse):
    submissions: list[SubmissionResponse] = []
    feedback: FeedbackResponse | None = None
