import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead, LeadStatus, Message, MessageDirection
import logging

logger = logging.getLogger(__name__)


def extract_phone(remote_jid: str) -> str:
    """Extract phone number from WhatsApp JID (e.g. '5511999999999@s.whatsapp.net')."""
    return remote_jid.split("@")[0]


def extract_message_text(message_dict: dict | None) -> str:
    """Extract text content from WhatsApp message payload."""
    if not message_dict:
        return ""
    # Common message types
    if "conversation" in message_dict:
        return message_dict["conversation"]
    if "extendedTextMessage" in message_dict:
        return message_dict["extendedTextMessage"].get("text", "")
    if "imageMessage" in message_dict:
        return message_dict["imageMessage"].get("caption", "[imagem]")
    if "videoMessage" in message_dict:
        return message_dict["videoMessage"].get("caption", "[vídeo]")
    if "documentMessage" in message_dict:
        return "[documento]"
    if "audioMessage" in message_dict:
        return "[áudio]"
    return "[mensagem não suportada]"


async def ingest_message(
    tenant_id: uuid.UUID,
    phone: str,
    push_name: str | None,
    content: str,
    from_me: bool,
    timestamp: datetime | None,
    db: AsyncSession,
) -> Message | None:
    """
    Process an incoming webhook message.
    - If lead doesn't exist, create with status=active.
    - If lead is converted/lost, discard message.
    - Otherwise, persist the message.
    Returns the persisted Message, or None if discarded.
    """
    result = await db.execute(
        select(Lead).where(Lead.tenant_id == tenant_id, Lead.phone == phone)
    )
    lead = result.scalar_one_or_none()
    # Never trust push_name from outbound messages (it is usually the operator/account owner).
    # Keep lead identity tied to inbound customer messages.
    lead_name_candidate = push_name if not from_me else None

    if lead is None:
        logger.info(
            "Creating new lead: tenant_id=%s phone=%s push_name=%s",
            tenant_id,
            phone,
            lead_name_candidate,
        )
        lead = Lead(
            tenant_id=tenant_id,
            phone=phone,
            name=lead_name_candidate,
            status=LeadStatus.active,
            is_processing=False,
        )
        db.add(lead)
        await db.flush()
    elif lead.status in (LeadStatus.converted, LeadStatus.lost):
        logger.warning(
            "Discarding message for lead in status: phone=%s status=%s",
            phone,
            lead.status,
        )
        return None

    # Update lead name only from inbound customer messages.
    if lead_name_candidate and not lead.name:
        lead.name = lead_name_candidate

    direction = MessageDirection.outbound if from_me else MessageDirection.inbound
    effective_timestamp = timestamp or datetime.now(timezone.utc)

    # Idempotency guard for provider retries with same logical message.
    if timestamp is not None:
        duplicate_result = await db.execute(
            select(Message)
            .where(
                Message.lead_id == lead.id,
                Message.direction == direction,
                Message.content == content,
                Message.timestamp == timestamp,
            )
            .limit(1)
        )
        duplicate = duplicate_result.scalar_one_or_none()
        if duplicate is not None:
            return duplicate

    msg = Message(
        lead_id=lead.id,
        direction=direction,
        content=content,
        timestamp=effective_timestamp,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


def ingest_message_sync(
    phone: str,
    push_name: str | None,
    content: str,
    from_me: bool,
    lead_status: str | None = None,
) -> dict:
    """Pure sync version for unit testing (no DB)."""
    if lead_status in ("converted", "lost"):
        return {"discarded": True, "reason": f"lead is {lead_status}"}

    direction = "outbound" if from_me else "inbound"
    return {
        "discarded": False,
        "phone": phone,
        "push_name": push_name,
        "content": content,
        "direction": direction,
        "is_new_lead": lead_status is None,
    }
