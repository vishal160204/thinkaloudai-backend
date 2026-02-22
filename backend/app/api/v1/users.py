"""
ThinkAloud.ai — User Profile Endpoints
"""
import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.session import Session
from app.schemas.user import UserProfileResponse, UserProfileUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads/avatars"


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return user


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile (username, full_name, bio, avatar_url)."""
    update_data = data.model_dump(exclude_unset=True)

    # Check username uniqueness if changing
    if "username" in update_data and update_data["username"] != user.username:
        result = await db.execute(
            select(User).where(User.username == update_data["username"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken")

    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/avatar", response_model=UserProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload avatar image. Max 2MB. Accepts png/jpg/webp."""
    # Validate file
    if file.content_type not in ["image/png", "image/jpeg", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, WEBP allowed")

    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:  # 2MB
        raise HTTPException(status_code=400, detail="File too large (max 2MB)")

    # Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1] if file.filename else "png"
    filename = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    # Update user
    user.avatar_url = f"/uploads/avatars/{filename}"
    await db.commit()
    await db.refresh(user)

    logger.info(f"Avatar uploaded for user {user.id}")
    return user


@router.get("/me/practice-time")
async def get_practice_time(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get total practice time in seconds."""
    result = await db.execute(
        select(func.coalesce(func.sum(Session.duration_seconds), 0))
        .where(Session.user_id == user.id, Session.status == "completed")
    )
    total_seconds = result.scalar()

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return {
        "total_seconds": total_seconds,
        "total_hours": hours,
        "total_minutes": minutes,
        "display": f"{hours}h {minutes}m",
    }
