"""
ThinkAloud.ai — Application Configuration
All settings loaded from environment variables via .env file.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Core
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # OTP
    otp_length: int = 6
    otp_expire_seconds: int = 300
    otp_max_attempts: int = 5
    otp_lockout_seconds: int = 900
    otp_resend_cooldown_seconds: int = 60

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "noreply@thinkaloudai.tech"

    # CORS (comma-separated origins)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # AI / vLLM
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model: str = "Qwen/Qwen3-32B"

    # LiveKit
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "thinkaloud_key"
    livekit_api_secret: str = "thinkaloud_secret_change_in_production"


settings = Settings()
