import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.redaction import mask_identifier
from app.models import SessionStatus, WhatsAppSession
from app.providers.whatsapp import get_whatsapp_provider
from app.services.webhook_service import (extract_message_text, extract_phone,
                                          ingest_message)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class ReplayGuard:
    def __init__(self):
        self._limiter = SlidingWindowRateLimiter()

    def seen_recently(self, key: str, window_seconds: int) -> bool:
        allowed, _ = self._limiter.hit(key, limit=1, window_seconds=window_seconds)
        if not allowed:
            return True
        return False


_replay_guard = ReplayGuard()
_webhook_limiter = SlidingWindowRateLimiter()


def _webhook_hmac_secret() -> str:
    return settings.WEBHOOK_HMAC_SECRET


def verify_webhook_signature(
    payload_body: bytes,
    signature: str | None,
    algorithm: str | None,
) -> bool:
    secret = _webhook_hmac_secret()
    if not secret:
        return True
    if not signature:
        return False
    if algorithm and algorithm.lower() != "sha512":
        return False

    expected = hmac.new(secret.encode(), payload_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def _parse_timestamp_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value.strip())
    except (TypeError, ValueError):
        return None
    if parsed > 10_000_000_000:
        parsed = parsed // 1000
    return parsed


def _is_timestamp_stale(ts_seconds: int, ttl_seconds: int) -> bool:
    now = int(time.time())
    return abs(now - ts_seconds) > ttl_seconds


def _to_session_status(event_name: str | None, payload: dict) -> SessionStatus | None:
    if event_name != "CONNECTION_UPDATE":
        return None

    data = payload.get("data") or {}
    raw_status = data.get("status") or data.get("state") or payload.get("status")
    status_map = {
        "PENDING": SessionStatus.PENDING,
        "QR_CODE_READY": SessionStatus.QR_CODE_READY,
        "QRCODE": SessionStatus.QR_CODE_READY,
        "CONNECTING": SessionStatus.CONNECTING,
        "OPEN": SessionStatus.CONNECTED,
        "CONNECTED": SessionStatus.CONNECTED,
        "CLOSED": SessionStatus.DISCONNECTED,
        "DISCONNECTED": SessionStatus.DISCONNECTED,
    }
    return status_map.get((raw_status or "").upper())


@router.post("/whatsapp")
async def webhook_whatsapp(
    request: Request,
    db: AsyncSession = Depends(get_db),
    provider=Depends(get_whatsapp_provider),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = _webhook_limiter.hit(
        f"webhook:{client_ip}",
        limit=settings.WEBHOOK_RATE_LIMIT,
        window_seconds=settings.WEBHOOK_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        logger.warning("webhook refused: rate limit exceeded ip=%s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    body = await request.body()
    if len(body) > settings.WEBHOOK_MAX_PAYLOAD_BYTES:
        logger.warning("webhook refused: payload too large size=%s", len(body))
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Payload too large")

    signature = request.headers.get("X-Webhook-Hmac") or request.headers.get("x-webhook-hmac")
    algorithm = request.headers.get("X-Webhook-Hmac-Algorithm") or request.headers.get("x-webhook-hmac-algorithm")
    request_id = request.headers.get("X-Webhook-Id") or request.headers.get("x-webhook-id")
    request_ts_raw = request.headers.get("X-Webhook-Timestamp") or request.headers.get("x-webhook-timestamp")
    request_ts = _parse_timestamp_seconds(request_ts_raw)

    if settings.WEBHOOK_REQUIRE_REPLAY_HEADERS and (not request_id or request_ts is None):
        logger.warning("webhook refused: missing replay headers")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing replay protection headers")

    if request_ts is not None and _is_timestamp_stale(
        request_ts,
        settings.WEBHOOK_REPLAY_TTL_SECONDS,
    ):
        logger.warning("webhook refused: stale timestamp")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stale webhook timestamp")

    if not verify_webhook_signature(body, signature, algorithm):
        logger.warning("webhook refused: invalid signature")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    event_name = payload.get("event")
    session_status = _to_session_status(event_name, payload)
    if session_status is not None:
        session_id = payload.get("instance") or payload.get("session")
        if not session_id:
            logger.warning("webhook refused: missing session id")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing session")

        replay_fingerprint = hashlib.sha256(body).hexdigest()
        replay_nonce = request_id or f"{event_name}:{replay_fingerprint}"
        replay_key = f"{session_id}:{replay_nonce}"
        if _replay_guard.seen_recently(
            replay_key,
            window_seconds=settings.WEBHOOK_REPLAY_TTL_SECONDS,
        ):
            logger.warning("webhook ignored: replay detected session_id=%s", mask_identifier(session_id))
            return {"status": "ignored", "reason": "replay detected"}

        result = await db.execute(
            select(WhatsAppSession).where(WhatsAppSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            logger.warning("webhook refused: unknown session_id=%s", mask_identifier(session_id))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown session")

        session.status = session_status
        if session_status == SessionStatus.CONNECTED and not session.connected_since:
            now = datetime.now(timezone.utc)
            session.connected_since = now
            session.connected_at = now
        elif session_status != SessionStatus.CONNECTED:
            session.connected_since = None
            session.connected_at = None

        await db.commit()
        await db.refresh(session)
        return {"status": "ok", "session_status": session.status.value}

    if event_name not in ("message.upsert", "message", "message.any"):
        return {"status": "ignored", "reason": f"event {event_name} not handled"}

    normalized = provider.normalize_webhook_payload(payload)
    if normalized is None:
        session_id = payload.get("session") or payload.get("instance")
        if not session_id:
            logger.warning("webhook refused: missing session id")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing session")
        return {"status": "ignored", "reason": "payload without remoteJid"}

    session_id = normalized.session_id
    replay_fingerprint = hashlib.sha256(body).hexdigest()
    replay_nonce = request_id or f"{normalized.message_id or ''}:{replay_fingerprint}"
    replay_key = f"{session_id}:{replay_nonce}"
    if _replay_guard.seen_recently(
        replay_key,
        window_seconds=settings.WEBHOOK_REPLAY_TTL_SECONDS,
    ):
        logger.warning("webhook ignored: replay detected session_id=%s", mask_identifier(session_id))
        return {"status": "ignored", "reason": "replay detected"}

    result = await db.execute(
        select(WhatsAppSession).where(WhatsAppSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        logger.warning("webhook refused: unknown session_id=%s", mask_identifier(session_id))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown session")

    metadata_tenant_id = normalized.metadata_tenant_id
    if metadata_tenant_id and str(session.tenant_id) != str(metadata_tenant_id):
        logger.warning("webhook refused: tenant mismatch session_id=%s", mask_identifier(session_id))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")

    phone = extract_phone(normalized.remote_jid)
    content = extract_message_text(normalized.content_payload)
    from_me = normalized.from_me
    push_name = normalized.push_name

    ts_raw = normalized.timestamp_raw
    ts = None
    if ts_raw:
        try:
            ts_int = int(ts_raw)
            if ts_int > 10_000_000_000:
                ts_int = ts_int // 1000
            ts = datetime.fromtimestamp(ts_int, tz=timezone.utc)
        except (TypeError, ValueError):
            ts = None

    msg = await ingest_message(
        tenant_id=session.tenant_id,
        phone=phone,
        push_name=push_name,
        content=content,
        from_me=from_me,
        timestamp=ts,
        db=db,
    )

    if msg is None:
        return {"status": "discarded", "reason": "lead not active"}

    return {"status": "ok", "message_id": str(msg.id)}
