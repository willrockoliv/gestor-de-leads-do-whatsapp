import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.webhook import WebhookPayload
from app.services.webhook_service import extract_phone, extract_message_text, ingest_message
from app.models import Tenant, WhatsAppSession

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_webhook_signature(payload_body: bytes, signature: str | None) -> bool:
    """Verify HMAC signature from WhatsApp API webhook."""
    if not settings.WHATSAPP_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured (dev mode)
    if not signature:
        return False
    expected = hmac.new(
        settings.WHATSAPP_WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/whatsapp")
async def webhook_whatsapp(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    signature = request.headers.get("x-webhook-signature")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = WebhookPayload.model_validate_json(body)

    if payload.event != "message.upsert":
        return {"status": "ignored", "reason": f"event {payload.event} not handled"}

    # Find the tenant by instance name (WhatsApp session)
    instance_name = payload.instance
    if instance_name:
        result = await db.execute(
            select(WhatsAppSession).where(WhatsAppSession.id == instance_name)
        )
        session = result.scalar_one_or_none()
        if session:
            tenant_id = session.tenant_id
        else:
            # Fallback: get first tenant (single-tenant dev mode)
            result = await db.execute(select(Tenant).limit(1))
            tenant = result.scalar_one_or_none()
            if not tenant:
                raise HTTPException(status_code=400, detail="No tenant found")
            tenant_id = tenant.id
    else:
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=400, detail="No tenant found")
        tenant_id = tenant.id

    phone = extract_phone(payload.data.key.remoteJid)
    content = extract_message_text(payload.data.message)
    from_me = payload.data.key.fromMe
    push_name = payload.data.pushName

    ts = None
    if payload.data.messageTimestamp:
        ts = datetime.fromtimestamp(payload.data.messageTimestamp, tz=timezone.utc)

    msg = await ingest_message(
        tenant_id=tenant_id,
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
