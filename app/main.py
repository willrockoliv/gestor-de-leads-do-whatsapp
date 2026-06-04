import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import analysis, auth, dashboard, tenants, webhooks, whatsapp

logger = logging.getLogger(__name__)
settings = get_settings()


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
            logger.error(f"Watchdog error: {e}")


async def whatsapp_sync_loop():
    """Background task to sync WhatsApp session status every 30 seconds."""
    from app.core.database import AsyncSessionLocal
    from app.services.whatsapp_session_service import sync_whatsapp_sessions

    while True:
        try:
            await asyncio.sleep(30)
            async with AsyncSessionLocal() as db:
                changed = await sync_whatsapp_sessions(db)
                if changed:
                    logger.info("WhatsApp sync: %s sessions updated", changed)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"WhatsApp sync error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    watchdog_task = asyncio.create_task(watchdog_loop())
    whatsapp_task = asyncio.create_task(whatsapp_sync_loop())
    yield
    watchdog_task.cancel()
    whatsapp_task.cancel()
    try:
        await watchdog_task
    except asyncio.CancelledError:
        pass
    try:
        await whatsapp_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
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
