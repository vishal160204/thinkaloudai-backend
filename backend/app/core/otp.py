from app.db.redis import get_redis
from app.config import settings
import secrets
import logging


logger = logging.getLogger(__name__)

def generate_otp() -> str:
    otp = "".join(str(secrets.randbelow(10)) for _ in range(settings.otp_length))
    return otp


async def save_otp(email: str, otp: str, purpose = "signup") -> None:

    redis = await get_redis()
    await redis.set(f"otp:{purpose}:{email}", otp, ex = settings.otp_expire_seconds)



async def check_resend_cooldown(email: str, purpose: str = "signup") -> bool:
    redis = await get_redis()
    ttl = await redis.ttl(f"otp:{pupose}:{email}")
    if ttl > (settings.otp_expire_seconds):
        return True
    return False

    

async def verify_otp(email: str, otp: str, purpose: str = "signup") -> bool:
    redis = await get_redis()
    lockout_key = f"otp:lockout:{purpose}:{email}"
    if await redis.exists(lockout_key):
        logger.warning(f"Otp verification locked out: {email}({purpose})")
        return False
    attempts_key = f"otp:attempts:{purpose}:{email}"
    attempts = int(await redis.get(attempts_key) or 0)
    if attempts >= settings.otp_max_attempts:
        await redis.set(lockout_key, "1", ex = settings.otp_lockout_seconds)
        await redis.delete(attempts_key)
        logger.warning(f"Otp max attempts reached, locking out:{email}:{purpose}")
        return False



    stored_otp  = await redis.get(f"otp:{purpose}:{email}")
    if stored_otp  and stored_otp == otp:
        await redis.delete(f"otp:{purpose}:{email}")
        await redis.delete(attempts_key)
        return True


    await redis.incr(attempts_key)
    await redis.expire(attempts_key, settings.otp_expire_seconds)
    return False
    







