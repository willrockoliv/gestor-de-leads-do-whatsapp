import hashlib
import hmac
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models import WhatsAppSession
from app.providers.whatsapp import get_whatsapp_provider
from app.services.webhook_service import (extract_message_text, extract_phone,
                                          ingest_message)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class ReplayGuard:
    def __init__(self):
        self._store: dict[str, deque[float]] = defaultdict(deque)

    def seen_recently(self, key: str, window_seconds: int) -> bool:
        now = time.time()
        bucket = self._store[key]

        while bucket and now - bucket[0] >= window_seconds:
            bucket.popleft()

        if bucket:
            return True

        bucket.append(now)
        return False


_replay_guard = ReplayGuard()


def _webhook_hmac_secret() -> str:
    return settings.WHATSAPP_WEBHOOK_HMAC_KEY or settings.WHATSAPP_WEBHOOK_SECRET


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


@router.post("/whatsapp")
async def webhook_whatsapp(
    request: Request,
    db: AsyncSession = Depends(get_db),
    provider=Depends(get_whatsapp_provider),
):
    body = await request.body()
    signature = request.headers.get("X-Webhook-Hmac") or request.headers.get("x-webhook-hmac")
    algorithm = request.headers.get("X-Webhook-Hmac-Algorithm") or request.headers.get("x-webhook-hmac-algorithm")

    if not verify_webhook_signature(body, signature, algorithm):
        logger.warning("webhook refused: invalid signature")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc
    event_name = payload.get("event")
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
    replay_key = f"{session_id}:{normalized.message_id or ''}:{replay_fingerprint}"
    if _replay_guard.seen_recently(replay_key, window_seconds=300):
        logger.warning("webhook ignored: replay detected session_id=%s", session_id)
        return {"status": "ignored", "reason": "replay detected"}

    result = await db.execute(
        select(WhatsAppSession).where(WhatsAppSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        logger.warning("webhook refused: unknown session_id=%s", session_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown session")

    metadata_tenant_id = normalized.metadata_tenant_id
    if metadata_tenant_id and str(session.tenant_id) != str(metadata_tenant_id):
        logger.warning("webhook refused: tenant mismatch session_id=%s", session_id)
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
