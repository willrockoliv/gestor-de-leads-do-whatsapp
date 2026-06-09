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
    WHATSAPP_PROVIDER: str = "waha"
    WHATSAPP_WEBHOOK_URL: str = ""
    WHATSAPP_WEBHOOK_REPLAY_TTL_SECONDS: int = 300
    WHATSAPP_WEBHOOK_REQUIRE_REPLAY_HEADERS: bool = False
    WHATSAPP_WEBHOOK_MAX_PAYLOAD_BYTES: int = 262144
    WHATSAPP_WEBHOOK_RATE_LIMIT: int = 300
    WHATSAPP_WEBHOOK_RATE_LIMIT_WINDOW_SECONDS: int = 60
    AUTH_LOGIN_RATE_LIMIT: int = 10
    AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Security headers
    SECURITY_CSP: str = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    SECURITY_REFERRER_POLICY: str = "no-referrer"
    SECURITY_PERMISSIONS_POLICY: str = "camera=(), microphone=(), geolocation=()"
    SECURITY_HSTS_MAX_AGE: int = 31536000
    SECURITY_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURITY_HSTS_PRELOAD: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
