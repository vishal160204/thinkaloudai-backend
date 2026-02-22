"""
ThinkAloud.ai — Authentication Endpoints
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.db import get_db
from app.db.redis import get_redis
from app.models.user import User
from app.schemas.auth import (
    SignupRequest, VerifyOTPRequest, ResendOTPRequest,
    LoginRequest, ForgotPasswordRequest, ResetPasswordRequest,
    RefreshTokenRequest, MessageResponse, TokenResponse
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.otp import generate_otp, save_otp, verify_otp, check_resend_cooldown
from app.core.email import send_otp_email
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Login brute-force protection ---

async def check_login_lockout(email: str) -> None:
    """Raise 429 if account is locked due to too many failed attempts."""
    redis = await get_redis()
    if await redis.exists(f"login:lockout:{email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again in 15 minutes.",
        )


async def record_failed_login(email: str) -> None:
    """Track failed login attempts. Lock out after 5 failures."""
    redis = await get_redis()
    key = f"login:attempts:{email}"
    attempts = await redis.incr(key)
    await redis.expire(key, settings.otp_lockout_seconds)
    if attempts >= settings.otp_max_attempts:
        await redis.set(f"login:lockout:{email}", "1", ex=settings.otp_lockout_seconds)
        await redis.delete(key)
        logger.warning(f"Login locked out: {email}")


async def clear_login_attempts(email: str) -> None:
    """Clear failed login tracking on successful login."""
    redis = await get_redis()
    await redis.delete(f"login:attempts:{email}")
    await redis.delete(f"login:lockout:{email}")


# --- Endpoints ---

@router.post("/signup", response_model=MessageResponse)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register new user — creates inactive account and sends OTP."""

    # Check if email exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.is_active:
            raise HTTPException(status_code=409, detail="Email already registered")
        # Delete unverified user for fresh signup
        await db.delete(existing_user)
        await db.commit()

    # Create user (inactive)
    user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        is_active=False,
    )
    try:
        db.add(user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email or username already taken")

    # Send OTP
    otp = generate_otp()
    await save_otp(data.email, otp, purpose="signup")
    await send_otp_email(to=data.email, otp=otp, purpose="signup")

    return {"message": "OTP sent to your email"}


@router.post("/verify-signup", response_model=TokenResponse)
async def verify_signup(data: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verify signup OTP and activate account."""

    if not await verify_otp(data.email, data.otp, purpose="signup"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/resend-signup-otp", response_model=MessageResponse)
async def resend_signup_otp(data: ResendOTPRequest, db: AsyncSession = Depends(get_db)):
    """Resend OTP with cooldown check."""

    # Check cooldown
    if await check_resend_cooldown(data.email, purpose="signup"):
        raise HTTPException(
            status_code=429,
            detail=f"Wait {settings.otp_resend_cooldown_seconds} seconds before resending",
        )

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or user.is_active:
        raise HTTPException(status_code=400, detail="No pending verification")

    otp = generate_otp()
    await save_otp(data.email, otp, purpose="signup")
    await send_otp_email(to=data.email, otp=otp, purpose="signup")

    return {"message": "OTP resent to your email"}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password. Includes brute-force protection."""

    await check_login_lockout(data.email)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password):
        await record_failed_login(data.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    # Success — clear lockout tracking and update last login
    await clear_login_attempts(data.email)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for new access + refresh tokens."""

    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset OTP."""

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        otp = generate_otp()
        await save_otp(data.email, otp, purpose="reset")
        await send_otp_email(to=data.email, otp=otp, purpose="reset")

    # Always return success (don't reveal if email exists)
    return {"message": "If email exists, OTP sent"}


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password with OTP verification."""

    if not await verify_otp(data.email, data.otp, purpose="reset"):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = hash_password(data.new_password)
    await db.commit()

    return {"message": "Password reset successful"}
