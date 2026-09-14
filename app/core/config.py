import truststore
truststore.inject_into_ssl()

"""
Centralized app configuration, loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM
    GOOGLE_Model: str = os.getenv("GOOGLE_Model", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    NOTIFY_TO_EMAIL: str = os.getenv("NOTIFY_TO_EMAIL", "")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")

    # JWT / approval tokens
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    APPROVAL_TOKEN_EXPIRE_HOURS: int = int(os.getenv("APPROVAL_TOKEN_EXPIRE_HOURS", 24))

    # LinkedIn
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_REDIRECT_URI: str = os.getenv("LINKEDIN_REDIRECT_URI", "")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    LINKEDIN_PERSON_URN: str = os.getenv("LINKEDIN_PERSON_URN", "")

    # App
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/linkedin_pipeline.db")

    # Duplicate-check tuning
    REFRESH_TOPIC_AFTER_DAYS: int = 90
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.85
    DAILY_TRIGGER_HOUR: int = int(os.getenv("DAILY_TRIGGER_HOUR", 16))
    DAILY_TRIGGER_MINUTE: int = int(os.getenv("DAILY_TRIGGER_MINUTE", 30))
    APPROVAL_TIMEOUT_HOURS: int = int(os.getenv("APPROVAL_TIMEOUT_HOURS", 4))
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    SESSION_TOKEN_EXPIRE_HOURS: int = int(os.getenv("SESSION_TOKEN_EXPIRE_HOURS",""))
    ENABLE_INPROCESS_SCHEDULER: bool = os.getenv("ENABLE_INPROCESS_SCHEDULER", "true").lower() == "true"


settings = Settings()
