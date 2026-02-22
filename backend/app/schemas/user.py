"""
ThinkAloud.ai — User Schemas
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    bio: str | None
    is_admin: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
