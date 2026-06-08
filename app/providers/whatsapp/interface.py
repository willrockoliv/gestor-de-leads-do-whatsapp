from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SessionStatus


class WhatsAppProviderError(RuntimeError):
    """Base error for provider integration failures."""


class WhatsAppProviderConflictError(WhatsAppProviderError):
    """Raised when provider constraints conflict with tenant/session model."""


class WhatsAppProviderUnavailableError(WhatsAppProviderError):
    """Raised when provider is unavailable after retries."""


class WhatsAppProviderAlreadyExistsError(WhatsAppProviderError):
    """Raised when provider session already exists remotely."""


@dataclass(slots=True)
class ProviderSessionStatus:
    status: SessionStatus
    phone_number: str | None = None


@dataclass(slots=True)
class NormalizedWebhookMessage:
    event_name: str
    session_id: str
    message_id: str | None
    remote_jid: str
    content_payload: dict | None
    push_name: str | None
    from_me: bool
    timestamp_raw: int | str | None
    metadata_tenant_id: str | None


class WhatsAppProvider(Protocol):
    async def resolve_session_id(self, tenant_id: UUID) -> str:
        ...

    async def create_session(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: str,
    ) -> None:
        ...

    async def fetch_qr_code(self, session_id: str) -> str | None:
        ...

    async def fetch_session_status(self, session_id: str) -> ProviderSessionStatus:
        ...

    async def stop_session(self, session_id: str) -> None:
        ...

    def normalize_webhook_payload(self, payload: dict) -> NormalizedWebhookMessage | None:
        ...
