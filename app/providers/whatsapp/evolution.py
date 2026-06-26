import asyncio
import logging
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import SessionStatus
from app.providers.whatsapp.interface import (
    NormalizedWebhookMessage,
    ProviderSessionStatus,
    WhatsAppProvider,
    WhatsAppProviderAlreadyExistsError,
    WhatsAppProviderError,
    WhatsAppProviderUnavailableError,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _to_internal_status(raw_status: str | None) -> SessionStatus:
    """Map Evolution API status to internal SessionStatus."""
    mapping = {
        "PENDING": SessionStatus.PENDING,
        "QR_CODE_READY": SessionStatus.QR_CODE_READY,
        "CONNECTING": SessionStatus.CONNECTING,
        "OPEN": SessionStatus.CONNECTED,
        "CONNECTED": SessionStatus.CONNECTED,
        "CLOSED": SessionStatus.DISCONNECTED,
        "DISCONNECTED": SessionStatus.DISCONNECTED,
    }
    return mapping.get((raw_status or "").upper(), SessionStatus.ERROR)


class EvolutionWhatsAppProvider(WhatsAppProvider):
    """WhatsApp provider adapter for Evolution API."""

    def __init__(self):
        if not settings.EVOLUTION_API_URL:
            raise ValueError(
                "EVOLUTION_API_URL is required when using Evolution provider. "
                "Set it in your environment variables or .env file."
            )
        if not settings.EVOLUTION_API_KEY:
            raise ValueError(
                "EVOLUTION_API_KEY is required when using Evolution provider. "
                "Set it in your environment variables or .env file."
            )
        self.base_url = settings.EVOLUTION_API_URL.rstrip("/")
        self.api_key = settings.EVOLUTION_API_KEY

    def _api_headers(self) -> dict[str, str]:
        """Build API headers for Evolution API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            # Evolution API v2 expects global auth on `apikey` header.
            headers["apikey"] = self.api_key
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
        """Execute HTTP request with exponential backoff retry logic."""
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
                # Detect conflict: instance already exists
                if exc.response.status_code == 409 or "already exists" in detail.lower():
                    raise WhatsAppProviderAlreadyExistsError(message) from exc
                if exc.response.status_code in (400, 401, 403, 404):
                    # Do not retry non-retriable client/auth errors.
                    raise WhatsAppProviderError(message) from exc
                last_exc = WhatsAppProviderError(message)
                if attempt >= attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                last_exc = exc
                if attempt >= attempts:
                    break
                await asyncio.sleep(2 ** (attempt - 1))

        raise WhatsAppProviderUnavailableError(
            f"Evolution API request failed after {attempts} attempts: {last_exc}"
        )

    async def resolve_session_id(self, tenant_id: UUID) -> str:
        """Resolve session ID for tenant (Evolution supports multiple instances per tenant)."""
        # Evolution API uses instance names; we use tenant-{tenant_id} format
        return f"tenant-{tenant_id}"

    async def create_session(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: str,
    ) -> None:
        """Create a new WhatsApp instance in Evolution API."""
        # Prepare payload for Evolution API
        payload = {
            "instanceName": session_id,
            "integration": "WHATSAPP-BAILEYS",
            "token": self.api_key,
            "rejectCall": False,
            "groupsIgnore": True,
            "rejectMsgs": [],
            "autoDownloadMedia": {
                "autoDownload": False
            },
            "webhook": {
                "url": settings.WEBHOOK_URL,
                "enabled": True,
                "webhook_by_events": False,
                "events": [
                    "QRCODE_UPDATED",
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE",
                    "MESSAGES_DELETE",
                    "MESSAGES_SET",
                    "SEND_MESSAGE",
                    "CONTACTS_SET",
                    "CONNECTION_UPDATE",
                ],
            } if settings.WEBHOOK_URL else None,
        }

        # Remove webhook section if URL is not configured
        if not settings.WEBHOOK_URL:
            payload.pop("webhook", None)

        # Create instance
        url = f"{self.base_url}/instance/create"
        await self._request_with_retry("POST", url, json_payload=payload)

    async def fetch_qr_code(self, session_id: str) -> str | None:
        """Fetch QR code for a session."""
        url = f"{self.base_url}/instance/connect/{session_id}"
        try:
            data = await self._request_with_retry("GET", url)
            # Evolution returns QR code in different formats
            qr = data.get("qr") or data.get("base64") or data.get("qrCode")
            return qr
        except WhatsAppProviderError:
            return None

    async def fetch_session_status(self, session_id: str) -> ProviderSessionStatus:
        """Fetch session status and phone number from Evolution API."""
        url = f"{self.base_url}/instance/connectionState/{session_id}"
        data = await self._request_with_retry("GET", url)

        # Extract status from instance data
        instance = data.get("instance") or {}
        status = instance.get("state") or data.get("status")

        # Extract phone number
        phone = instance.get("phoneNumber") or instance.get("phone") or data.get("phone")
        phone_normalized = str(phone).lstrip("+") if phone else None

        return ProviderSessionStatus(
            status=_to_internal_status(status),
            phone_number=phone_normalized,
        )

    async def stop_session(self, session_id: str) -> None:
        """Stop/disconnect a WhatsApp instance."""
        url = f"{self.base_url}/instance/logout/{session_id}"
        await self._request_with_retry("DELETE", url)

    def normalize_webhook_payload(self, payload: dict) -> NormalizedWebhookMessage | None:
        """Normalize Evolution API webhook payload to internal format."""
        # Evolution sends events with event type in top-level key
        event_type = payload.get("event")
        event_type_normalized = None
        if isinstance(event_type, str):
            event_type_normalized = event_type.strip().upper().replace(".", "_").replace("-", "_")

        # When webhook_by_events=true some deployments may omit top-level `event`.
        # In that case we try to infer message payload shape instead of rejecting early.
        if event_type is not None and event_type_normalized not in ("MESSAGES_UPSERT", "MESSAGES_UPDATE"):
            logger.debug("Evolution webhook event not a message: event_type=%s", event_type)
            return None

        # Extract instance name (session_id)
        instance_name = (
            payload.get("instance")
            or payload.get("instanceName")
            or payload.get("session")
        )
        if not instance_name:
            logger.warning("Evolution webhook: missing instance name")
            return None

        # Extract message data from wrapped or raw payload formats.
        data = payload.get("data") or {}
        messages = data.get("messages") or []
        if messages:
            message = messages[0]
        elif isinstance(data.get("key"), dict):
            message = data
        elif isinstance(payload.get("key"), dict):
            message = payload
        else:
            logger.warning("Evolution webhook: no messages in data")
            return None

        key = message.get("key") or {}
        remote_jid = key.get("remoteJid")
        remote_jid_alt = key.get("remoteJidAlt")
        if remote_jid and remote_jid.endswith("@lid") and remote_jid_alt:
            remote_jid = remote_jid_alt
        elif not remote_jid:
            remote_jid = remote_jid_alt
        if not remote_jid:
            logger.warning("Evolution webhook: missing remoteJid")
            return None

        # Extract message metadata
        message_body = message.get("message") or {}
        timestamp = message.get("messageTimestamp") or data.get("messageTimestamp") or payload.get("messageTimestamp")

        return NormalizedWebhookMessage(
            event_name="message.upsert",
            session_id=instance_name,
            message_id=key.get("id"),
            remote_jid=remote_jid,
            content_payload=message_body,
            push_name=message.get("pushName") or payload.get("pushName"),
            from_me=bool(key.get("fromMe", False)),
            timestamp_raw=timestamp,
            metadata_tenant_id=None,  # Evolution doesn't provide tenant_id in webhook
        )
