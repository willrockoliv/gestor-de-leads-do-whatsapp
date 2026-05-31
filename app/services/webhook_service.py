import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lead, LeadStatus, Message, MessageDirection


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

    if lead is None:
        lead = Lead(
            tenant_id=tenant_id,
            phone=phone,
            name=push_name,
            status=LeadStatus.active,
            is_processing=False,
        )
        db.add(lead)
        await db.flush()
    elif lead.status in (LeadStatus.converted, LeadStatus.lost):
        return None

    # Update lead name if we have pushName and it's not set
    if push_name and not lead.name:
        lead.name = push_name

    direction = MessageDirection.outbound if from_me else MessageDirection.inbound
    msg = Message(
        lead_id=lead.id,
        direction=direction,
        content=content,
        timestamp=timestamp or datetime.now(timezone.utc),
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
