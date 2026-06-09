import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redaction import mask_identifier, sanitize_error_message
from app.models import Lead, SessionStatus, WhatsAppSession
from app.providers.whatsapp import (WhatsAppProvider,
                                    WhatsAppProviderAlreadyExistsError,
                                    get_whatsapp_provider)

logger = logging.getLogger(__name__)


class WhatsAppSessionService:
    def __init__(self, db: AsyncSession, provider: WhatsAppProvider | None = None):
        self.db = db
        self.provider = provider or get_whatsapp_provider()

    async def create_session(self, tenant_id: UUID) -> WhatsAppSession:
        existing = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.tenant_id == tenant_id).limit(1)
        )
        session = existing.scalar_one_or_none()
        if session:
            return session

        session_id = await self.provider.resolve_session_id(tenant_id)

        try:
            await self.provider.create_session(self.db, tenant_id, session_id)
        except WhatsAppProviderAlreadyExistsError:
            pass

        session = WhatsAppSession(
            tenant_id=tenant_id,
            session_id=session_id,
            status=SessionStatus.PENDING,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            "whatsapp session created tenant_id=%s session_id=%s",
            mask_identifier(tenant_id),
            mask_identifier(session_id),
        )
        return session

    async def get_qr_code(self, session: WhatsAppSession) -> WhatsAppSession:
        qr_value = await self.provider.fetch_qr_code(session.session_id)
        if qr_value:
            session.qr_code = qr_value
            session.qr_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            session.status = SessionStatus.QR_CODE_READY
            await self.db.commit()
            await self.db.refresh(session)

        return session

    async def check_connection_status(self, session: WhatsAppSession) -> WhatsAppSession:
        provider_status = await self.provider.fetch_session_status(session.session_id)
        session.status = provider_status.status

        if provider_status.phone_number:
            session.phone_number = provider_status.phone_number

        if session.status == SessionStatus.CONNECTED and not session.connected_since:
            session.connected_since = datetime.now(timezone.utc)
            session.connected_at = session.connected_since

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def disconnect_session(self, session: WhatsAppSession) -> WhatsAppSession:
        await self.provider.stop_session(session.session_id)

        session.status = SessionStatus.DISCONNECTED
        session.qr_code = None
        session.qr_code_expires_at = None
        session.connected_since = None
        session.connected_at = None
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def update_session_from_api(self, session: WhatsAppSession) -> WhatsAppSession:
        return await self.check_connection_status(session)


async def sync_whatsapp_sessions(db: AsyncSession, provider: WhatsAppProvider | None = None) -> int:
    service = WhatsAppSessionService(db, provider=provider)
    result = await db.execute(select(WhatsAppSession))
    sessions = result.scalars().all()

    changed = 0
    for session in sessions:
        old_status = session.status
        try:
            await service.update_session_from_api(session)
            if session.status != old_status:
                changed += 1
                logger.info(
                    "whatsapp session status changed tenant_id=%s session_id=%s old=%s new=%s",
                    mask_identifier(session.tenant_id),
                    mask_identifier(session.session_id),
                    old_status.value,
                    session.status.value,
                )
            if session.status == SessionStatus.DISCONNECTED:
                await db.execute(
                    Lead.__table__.update()
                    .where(Lead.tenant_id == session.tenant_id, Lead.is_processing.is_(True))
                    .values(is_processing=False)
                )
                await db.commit()
        except Exception as exc:
            logger.error(
                "failed to sync whatsapp session tenant_id=%s session_id=%s error=%s",
                mask_identifier(session.tenant_id),
                mask_identifier(session.session_id),
                sanitize_error_message(exc),
            )

    return changed
