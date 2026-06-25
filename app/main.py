import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.core.redaction import sanitize_error_message
from app.routers import analysis, auth, dashboard, tenants, webhooks, whatsapp

settings = get_settings()
configure_logging(use_json=settings.LOG_JSON, level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


async def watchdog_loop():
    """Background task to reset zombie locks every 60 seconds."""
    from app.core.database import AsyncSessionLocal
    from app.services.analysis_service import reset_zombie_locks

    while True:
        try:
            await asyncio.sleep(60)
            async with AsyncSessionLocal() as db:
                count = await reset_zombie_locks(db)
                if count:
                    logger.warning(f"Watchdog: reset {count} zombie locks")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Watchdog error: %s", sanitize_error_message(e))


async def analysis_queue_loop(worker_id: int):
    """Background worker that processes pending lead analysis."""
    from app.core.database import AsyncSessionLocal
    from app.services.analysis_service import process_next_pending_lead

    while True:
        try:
            async with AsyncSessionLocal() as db:
                processed = await process_next_pending_lead(db)
            await asyncio.sleep(1 if processed else 2)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(
                "Analysis queue worker %s error: %s",
                worker_id,
                sanitize_error_message(e),
            )
            await asyncio.sleep(2)


async def whatsapp_sync_loop():
    """Background task to sync WhatsApp session status every 30 seconds."""
    from app.core.database import AsyncSessionLocal
    from app.providers.whatsapp import get_whatsapp_provider
    from app.services.whatsapp_session_service import sync_whatsapp_sessions

    provider = get_whatsapp_provider()

    while True:
        try:
            await asyncio.sleep(30)
            async with AsyncSessionLocal() as db:
                changed = await sync_whatsapp_sessions(db, provider=provider)
                if changed:
                    logger.info("WhatsApp sync: %s sessions updated", changed)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("WhatsApp sync error: %s", sanitize_error_message(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    watchdog_task = asyncio.create_task(watchdog_loop())
    worker_count = max(settings.ANALYSIS_WORKER_CONCURRENCY, 1)
    analysis_queue_tasks = [
        asyncio.create_task(analysis_queue_loop(worker_id=i + 1))
        for i in range(worker_count)
    ]
    whatsapp_task = asyncio.create_task(whatsapp_sync_loop())
    yield
    watchdog_task.cancel()
    for task in analysis_queue_tasks:
        task.cancel()
    whatsapp_task.cancel()
    try:
        await watchdog_task
    except asyncio.CancelledError:
        pass
    for task in analysis_queue_tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass
    try:
        await whatsapp_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)


def _hsts_value() -> str:
    value = f"max-age={settings.SECURITY_HSTS_MAX_AGE}"
    if settings.SECURITY_HSTS_INCLUDE_SUBDOMAINS:
        value += "; includeSubDomains"
    if settings.SECURITY_HSTS_PRELOAD:
        value += "; preload"
    return value


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = settings.SECURITY_REFERRER_POLICY
    response.headers["Permissions-Policy"] = settings.SECURITY_PERMISSIONS_POLICY
    response.headers["Content-Security-Policy"] = settings.SECURITY_CSP
    response.headers["Strict-Transport-Security"] = _hsts_value()
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(whatsapp.router)
app.include_router(webhooks.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
