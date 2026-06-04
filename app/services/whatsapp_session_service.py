import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Lead, SessionStatus, WhatsAppSession

logger = logging.getLogger(__name__)
settings = get_settings()


def _api_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if settings.WHATSAPP_API_KEY:
        headers["X-Api-Key"] = settings.WHATSAPP_API_KEY
    return headers


def _to_internal_status(raw_status: str | None) -> SessionStatus:
    mapping = {
        "STARTING": SessionStatus.CONNECTING,
        "SCAN_QR_CODE": SessionStatus.QR_CODE_READY,
        "WORKING": SessionStatus.CONNECTED,
        "STOPPED": SessionStatus.DISCONNECTED,
        "FAILED": SessionStatus.ERROR,
        "PENDING": SessionStatus.PENDING,
        "QR_CODE_READY": SessionStatus.QR_CODE_READY,
        "CONNECTING": SessionStatus.CONNECTING,
        "CONNECTED": SessionStatus.CONNECTED,
        "DISCONNECTED": SessionStatus.DISCONNECTED,
        "ERROR": SessionStatus.ERROR,
    }
    return mapping.get((raw_status or "").upper(), SessionStatus.ERROR)


class WhatsAppSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_url = settings.WHATSAPP_API_URL.rstrip("/")

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        json: dict | None = None,
        attempts: int = 3,
        timeout_seconds: int = 10,
    ) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=_api_headers(),
                        json=json,
                    )
                response.raise_for_status()
                if not response.content:
                    return {}
                return response.json()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                last_exc = RuntimeError(f"HTTP {exc.response.status_code}: {detail}")
                if attempt >= attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                last_exc = exc
                if attempt >= attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))

        raise RuntimeError(f"WAHA request failed: {last_exc}")

    async def _resolve_session_id(self, tenant_id: UUID) -> str:
        """Resolve session name based on WAHA tier (CORE supports only 'default')."""
        try:
            version_info = await self._request_with_retry("GET", f"{self.base_url}/api/version")
        except RuntimeError:
            try:
                env = await self._request_with_retry("GET", f"{self.base_url}/api/server/environment")
                tier = str(env.get("WAHA_TIER", "")).upper()
                if tier == "CORE":
                    return "default"
            except RuntimeError:
                pass
            return f"tenant-{tenant_id}"

        tier = str(version_info.get("tier", "")).upper()
        if tier == "CORE":
            return "default"
        return f"tenant-{tenant_id}"

    async def create_session(self, tenant_id: UUID) -> WhatsAppSession:
        existing = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.tenant_id == tenant_id).limit(1)
        )
        session = existing.scalar_one_or_none()
        if session:
            return session

        session_id = await self._resolve_session_id(tenant_id)

        if session_id == "default":
            existing_default = await self.db.execute(
                select(WhatsAppSession).where(
                    WhatsAppSession.session_id == "default",
                    WhatsAppSession.tenant_id != tenant_id,
                )
            )
            if existing_default.scalar_one_or_none() is not None:
                raise RuntimeError(
                    "WAHA CORE only supports a single shared session (default). "
                    "Upgrade to WAHA PLUS for one session per tenant."
                )
        payload = {
            "name": session_id,
            "config": {
                "webhooks": [
                    {
                        "url": settings.WHATSAPP_WEBHOOK_URL,
                        "events": ["message", "message.any", "session.status"],
                        "hmac": {"key": settings.WHATSAPP_WEBHOOK_HMAC_KEY}
                        if settings.WHATSAPP_WEBHOOK_HMAC_KEY
                        else None,
                    }
                ]
            },
        }

        webhooks = payload["config"]["webhooks"]
        if not settings.WHATSAPP_WEBHOOK_URL:
            payload = {"name": session_id}
        elif webhooks[0].get("hmac") is None:
            del webhooks[0]["hmac"]

        try:
            await self._request_with_retry("POST", f"{self.base_url}/api/sessions", json=payload)
        except RuntimeError as exc:
            if "already exists" not in str(exc):
                raise

        session = WhatsAppSession(
            tenant_id=tenant_id,
            session_id=session_id,
            status=SessionStatus.PENDING,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info("whatsapp session created tenant_id=%s session_id=%s", tenant_id, session_id)
        return session

    async def get_qr_code(self, session: WhatsAppSession) -> WhatsAppSession:
        data = await self._request_with_retry(
            "GET",
            f"{self.base_url}/api/{session.session_id}/auth/qr",
        )

        qr_value = data.get("value") or data.get("qr") or data.get("qrCode")
        if qr_value:
            session.qr_code = qr_value
            session.qr_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            session.status = SessionStatus.QR_CODE_READY
            await self.db.commit()
            await self.db.refresh(session)

        return session

    async def check_connection_status(self, session: WhatsAppSession) -> WhatsAppSession:
        data = await self._request_with_retry(
            "GET",
            f"{self.base_url}/api/sessions/{session.session_id}",
        )

        raw_status = data.get("status")
        session.status = _to_internal_status(raw_status)

        me = data.get("me") or {}
        phone = me.get("id") or data.get("phone") or data.get("phoneNumber")
        if phone:
            session.phone_number = str(phone).split("@")[0]

        if session.status == SessionStatus.CONNECTED and not session.connected_since:
            session.connected_since = datetime.now(timezone.utc)
            session.connected_at = session.connected_since

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def disconnect_session(self, session: WhatsAppSession) -> WhatsAppSession:
        await self._request_with_retry(
            "POST",
            f"{self.base_url}/api/sessions/{session.session_id}/stop",
            json={},
        )

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


async def sync_whatsapp_sessions(db: AsyncSession) -> int:
    service = WhatsAppSessionService(db)
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
                    session.tenant_id,
                    session.session_id,
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
                session.tenant_id,
                session.session_id,
                exc,
            )

    return changed
