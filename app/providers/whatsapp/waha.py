import asyncio
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import SessionStatus, WhatsAppSession
from app.providers.whatsapp.interface import (NormalizedWebhookMessage,
                                              ProviderSessionStatus,
                                              WhatsAppProvider,
                                              WhatsAppProviderAlreadyExistsError,
                                              WhatsAppProviderConflictError,
                                              WhatsAppProviderError,
                                              WhatsAppProviderUnavailableError)

settings = get_settings()


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


class WahaWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        self.base_url = settings.WAHA_API_URL.rstrip("/")

    def _api_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if settings.WAHA_API_KEY:
            headers["X-Api-Key"] = settings.WAHA_API_KEY
        return headers

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        json_payload: dict | None = None,
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
                        headers=self._api_headers(),
                        json=json_payload,
                    )
                response.raise_for_status()
                if not response.content:
                    return {}
                return response.json()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                message = f"HTTP {exc.response.status_code}: {detail}"
                if "already exists" in detail.lower():
                    raise WhatsAppProviderAlreadyExistsError(message) from exc
                last_exc = WhatsAppProviderError(message)
                if attempt >= attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                last_exc = exc
                if attempt >= attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))

        raise WhatsAppProviderUnavailableError(f"WAHA request failed: {last_exc}")

    async def resolve_session_id(self, tenant_id: UUID) -> str:
        """Resolve session id based on WAHA tier (CORE supports only default)."""
        try:
            version_info = await self._request_with_retry("GET", f"{self.base_url}/api/version")
        except WhatsAppProviderUnavailableError:
            try:
                env = await self._request_with_retry("GET", f"{self.base_url}/api/server/environment")
                tier = str(env.get("WAHA_TIER", "")).upper()
                if tier == "CORE":
                    return "default"
            except WhatsAppProviderUnavailableError:
                pass
            return f"tenant-{tenant_id}"

        tier = str(version_info.get("tier", "")).upper()
        if tier == "CORE":
            return "default"
        return f"tenant-{tenant_id}"

    async def _validate_session_creation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: str,
    ) -> None:
        if session_id != "default":
            return

        existing_default = await db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.session_id == "default",
                WhatsAppSession.tenant_id != tenant_id,
            )
        )
        if existing_default.scalar_one_or_none() is not None:
            raise WhatsAppProviderConflictError(
                "WAHA CORE only supports a single shared session (default). "
                "Upgrade to WAHA PLUS for one session per tenant."
            )

    async def create_session(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: str,
    ) -> None:
        await self._validate_session_creation(db, tenant_id, session_id)

        payload = {
            "name": session_id,
            "config": {
                "webhooks": [
                    {
                        "url": settings.WEBHOOK_URL,
                        "events": ["message", "message.any", "session.status"],
                        "hmac": {"key": settings.WEBHOOK_HMAC_SECRET}
                        if settings.WEBHOOK_HMAC_SECRET
                        else None,
                    }
                ]
            },
        }

        webhooks = payload["config"]["webhooks"]
        if not settings.WEBHOOK_URL:
            payload = {"name": session_id}
        elif webhooks[0].get("hmac") is None:
            del webhooks[0]["hmac"]

        await self._request_with_retry("POST", f"{self.base_url}/api/sessions", json_payload=payload)

    async def fetch_qr_code(self, session_id: str) -> str | None:
        data = await self._request_with_retry("GET", f"{self.base_url}/api/{session_id}/auth/qr")
        return data.get("value") or data.get("qr") or data.get("qrCode")

    async def fetch_session_status(self, session_id: str) -> ProviderSessionStatus:
        data = await self._request_with_retry("GET", f"{self.base_url}/api/sessions/{session_id}")
        me = data.get("me") or {}
        phone = me.get("id") or data.get("phone") or data.get("phoneNumber")
        phone_normalized = str(phone).split("@")[0] if phone else None
        return ProviderSessionStatus(
            status=_to_internal_status(data.get("status")),
            phone_number=phone_normalized,
        )

    async def stop_session(self, session_id: str) -> None:
        await self._request_with_retry(
            "POST",
            f"{self.base_url}/api/sessions/{session_id}/stop",
            json_payload={},
        )

    def normalize_webhook_payload(self, payload: dict) -> NormalizedWebhookMessage | None:
        event_name = payload.get("event")
        if event_name not in ("message.upsert", "message", "message.any"):
            return None

        session_id = payload.get("session") or payload.get("instance")
        if not session_id:
            return None

        metadata = payload.get("metadata") or {}
        data = payload.get("data") or payload.get("payload") or {}
        key = data.get("key") or {}
        remote_jid = key.get("remoteJid") or data.get("from")
        if not remote_jid:
            return None

        return NormalizedWebhookMessage(
            event_name=event_name,
            session_id=session_id,
            message_id=key.get("id") or data.get("id"),
            remote_jid=remote_jid,
            content_payload=data.get("message"),
            push_name=data.get("pushName"),
            from_me=bool(key.get("fromMe", data.get("fromMe", False))),
            timestamp_raw=data.get("messageTimestamp") or payload.get("timestamp"),
            metadata_tenant_id=metadata.get("tenant_id"),
        )
