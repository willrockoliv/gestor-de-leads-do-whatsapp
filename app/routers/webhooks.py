import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models import WhatsAppSession
from app.services.webhook_service import (extract_message_text, extract_phone,
                                          ingest_message)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


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

    session_id = payload.get("session") or payload.get("instance")
    if not session_id:
        logger.warning("webhook refused: missing session id")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing session")

    result = await db.execute(
        select(WhatsAppSession).where(WhatsAppSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        logger.warning("webhook refused: unknown session_id=%s", session_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown session")

    metadata = payload.get("metadata") or {}
    metadata_tenant_id = metadata.get("tenant_id")
    if metadata_tenant_id and str(session.tenant_id) != str(metadata_tenant_id):
        logger.warning("webhook refused: tenant mismatch session_id=%s", session_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")

    data = payload.get("data") or payload.get("payload") or {}
    key = data.get("key") or {}
    remote_jid = key.get("remoteJid") or data.get("from")
    if not remote_jid:
        return {"status": "ignored", "reason": "payload without remoteJid"}

    phone = extract_phone(remote_jid)
    content = extract_message_text(data.get("message"))
    from_me = bool(key.get("fromMe", data.get("fromMe", False)))
    push_name = data.get("pushName")

    ts_raw = data.get("messageTimestamp") or payload.get("timestamp")
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
