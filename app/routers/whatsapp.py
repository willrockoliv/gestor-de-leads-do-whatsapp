import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import SessionStatus, User, WhatsAppSession
from app.providers.whatsapp import (WhatsAppProviderConflictError,
                                    WhatsAppProviderError,
                                    get_whatsapp_provider)
from app.schemas.whatsapp import (ConnectionStatusResponse, QRCodeResponse,
                                  WhatsAppSessionResponse)
from app.services.whatsapp_session_service import WhatsAppSessionService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)


class TenantRateLimiter:
    def __init__(self):
        self._store: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        bucket = self._store[key]

        while bucket and now - bucket[0] >= window_seconds:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, int(window_seconds - (now - bucket[0])))
            return False, retry_after

        bucket.append(now)
        return True, 0


_limiter = TenantRateLimiter()


async def _get_session_for_tenant(db: AsyncSession, tenant_id: UUID) -> WhatsAppSession | None:
    result = await db.execute(
        select(WhatsAppSession).where(WhatsAppSession.tenant_id == tenant_id).limit(1)
    )
    return result.scalar_one_or_none()


def get_whatsapp_service(
    db: AsyncSession = Depends(get_db),
    provider=Depends(get_whatsapp_provider),
) -> WhatsAppSessionService:
    return WhatsAppSessionService(db=db, provider=provider)


@router.post("/connect", response_model=WhatsAppSessionResponse)
async def connect_whatsapp(
    current_user: User = Depends(get_current_user),
    service: WhatsAppSessionService = Depends(get_whatsapp_service),
):
    allowed, retry_after = _limiter.hit(f"connect:{current_user.tenant_id}", limit=5, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        session = await service.create_session(current_user.tenant_id)
    except WhatsAppProviderConflictError as exc:
        message = str(exc)
        logger.error("whatsapp connect failed tenant_id=%s error=%s", current_user.tenant_id, message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc
    except WhatsAppProviderError as exc:
        message = str(exc)
        logger.error("whatsapp connect failed tenant_id=%s error=%s", current_user.tenant_id, message)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao criar sessão no serviço WhatsApp",
        ) from exc

    return WhatsAppSessionResponse(session_id=session.session_id, status=session.status.value)


@router.get("/qrcode", response_model=QRCodeResponse)
async def get_whatsapp_qrcode(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppSessionService = Depends(get_whatsapp_service),
):
    allowed, retry_after = _limiter.hit(f"qrcode:{current_user.tenant_id}", limit=20, window_seconds=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    session = await _get_session_for_tenant(db, current_user.tenant_id)
    if not session:
        raise HTTPException(status_code=404, detail="Nenhuma sessão WhatsApp ativa")

    if session.status == SessionStatus.CONNECTED:
        return QRCodeResponse(status=session.status.value, phone=session.phone_number)

    expires_at = session.qr_code_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        now_ref = datetime.now(timezone.utc)
    else:
        now_ref = datetime.now(timezone.utc)

    if not expires_at or expires_at <= now_ref:
        try:
            session = await service.get_qr_code(session)
        except WhatsAppProviderError as exc:
            logger.error("whatsapp qrcode failed tenant_id=%s error=%s", current_user.tenant_id, exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Falha ao obter QR code no serviço WhatsApp",
            ) from exc

    return QRCodeResponse(status=session.status.value, qr_code=session.qr_code, phone=session.phone_number)


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_whatsapp_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: WhatsAppSessionService = Depends(get_whatsapp_service),
):
    session = await _get_session_for_tenant(db, current_user.tenant_id)
    if not session:
        return ConnectionStatusResponse(status=SessionStatus.DISCONNECTED.value)

    try:
        session = await service.check_connection_status(session)
    except WhatsAppProviderError as exc:
        logger.error("whatsapp status failed tenant_id=%s error=%s", current_user.tenant_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Falha ao consultar status no serviço WhatsApp",
        ) from exc

    return ConnectionStatusResponse(
        status=session.status.value,
        phone=session.phone_number,
        connected_since=session.connected_since,
    )
