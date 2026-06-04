from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Gestor de Leads do WhatsApp"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/leads"

    # JWT
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # LLM
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    # WhatsApp
    WHATSAPP_WEBHOOK_SECRET: str = ""
    WHATSAPP_WEBHOOK_HMAC_KEY: str = ""
    WHATSAPP_API_URL: str = "http://waha:3000"
    WHATSAPP_API_PORT: int = 3000
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_WEBHOOK_URL: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
