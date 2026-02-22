"""
ThinkAloud.ai — Email Service
Uses Resend for production, logs to console in dev.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, body: str):
    """Send email via Resend API, or log in dev mode."""
    if settings.debug or not settings.resend_api_key:
        logger.info(f"📧 [DEV] To: {to} | Subject: {subject}\n{body}")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.email_from,
                    "to": [to],
                    "subject": subject,
                    "html": body,
                },
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"✅ Email sent to {to}")
    except Exception as e:
        logger.error(f"❌ Email failed to {to}: {e}")
        # Don't raise — email failure shouldn't block the user


async def send_otp_email(to: str, otp: str, purpose: str = "signup"):
    """Send OTP email with a nice template."""
    if purpose == "signup":
        subject = "ThinkAloud.ai — Verify Your Email"
        body = f"""
        <h2>Welcome to ThinkAloud.ai! 🎯</h2>
        <p>Your verification code is:</p>
        <h1 style="letter-spacing: 8px; font-size: 36px; color: #6C5CE7;">{otp}</h1>
        <p>This code expires in 5 minutes. Do not share it with anyone.</p>
        <p>— The ThinkAloud.ai Team</p>
        """
    else:
        subject = "ThinkAloud.ai — Password Reset Code"
        body = f"""
        <h2>Password Reset Request 🔑</h2>
        <p>Your reset code is:</p>
        <h1 style="letter-spacing: 8px; font-size: 36px; color: #6C5CE7;">{otp}</h1>
        <p>This code expires in 5 minutes. If you didn't request this, ignore this email.</p>
        <p>— The ThinkAloud.ai Team</p>
        """

    await send_email(to, subject, body)
