"""Unit tests for Evolution API WhatsApp provider."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.providers.whatsapp.evolution import EvolutionWhatsAppProvider
from app.providers.whatsapp.interface import (
    ProviderSessionStatus,
    WhatsAppProviderAlreadyExistsError,
    WhatsAppProviderError,
    WhatsAppProviderUnavailableError,
)
from app.models import SessionStatus


@pytest.fixture
def evolution_provider():
    """Create an Evolution API provider instance."""
    with patch("app.providers.whatsapp.evolution.get_settings") as mock_settings:
        mock_settings.return_value.EVOLUTION_API_URL = "http://evolution-api:8080"
        mock_settings.return_value.EVOLUTION_API_KEY = "test-api-key"
        mock_settings.return_value.WEBHOOK_URL = "http://localhost:8000/webhooks/whatsapp"
        provider = EvolutionWhatsAppProvider()
        provider.api_key = "test-api-key"
    return provider


@pytest.mark.asyncio
async def test_resolve_session_id():
    """Test that resolve_session_id generates correct session ID."""
    provider = EvolutionWhatsAppProvider()
    tenant_id = uuid4()
    session_id = await provider.resolve_session_id(tenant_id)
    assert session_id == f"tenant-{tenant_id}"


@pytest.mark.asyncio
async def test_create_session(evolution_provider):
    """Test session creation with Evolution API."""
    tenant_id = uuid4()
    session_id = f"tenant-{tenant_id}"

    mock_db = AsyncMock()

    with patch.object(evolution_provider, "_request_with_retry", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"instance_id": session_id}
        await evolution_provider.create_session(mock_db, tenant_id, session_id)

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "/instance/create" in call_args[0][1]

        payload = call_args[1]["json_payload"]
        assert payload["instanceName"] == session_id
        assert payload["integration"] == "WHATSAPP-BAILEYS"


@pytest.mark.asyncio
async def test_create_session_already_exists(evolution_provider):
    """Test handling of session already existing error."""
    tenant_id = uuid4()
    session_id = f"tenant-{tenant_id}"

    mock_db = AsyncMock()

    with patch.object(
        evolution_provider,
        "_request_with_retry",
        side_effect=WhatsAppProviderAlreadyExistsError("Instance already exists"),
    ):
        with pytest.raises(WhatsAppProviderAlreadyExistsError):
            await evolution_provider.create_session(mock_db, tenant_id, session_id)


@pytest.mark.asyncio
async def test_fetch_qr_code(evolution_provider):
    """Test QR code fetching."""
    session_id = "tenant-test"
    expected_qr = "base64_encoded_qr_code_here"

    with patch.object(evolution_provider, "_request_with_retry", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"qr": expected_qr}
        result = await evolution_provider.fetch_qr_code(session_id)
        assert result == expected_qr


@pytest.mark.asyncio
async def test_fetch_qr_code_not_available(evolution_provider):
    """Test QR code fetch when provider error occurs."""
    session_id = "tenant-test"

    with patch.object(
        evolution_provider,
        "_request_with_retry",
        side_effect=WhatsAppProviderError("QR code not ready"),
    ):
        result = await evolution_provider.fetch_qr_code(session_id)
        assert result is None


@pytest.mark.asyncio
async def test_fetch_session_status(evolution_provider):
    """Test fetching session status."""
    session_id = "tenant-test"

    with patch.object(evolution_provider, "_request_with_retry", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "instance": {
                "state": "OPEN",
                "phoneNumber": "5511999999999",
            }
        }
        result = await evolution_provider.fetch_session_status(session_id)

        assert isinstance(result, ProviderSessionStatus)
        assert result.status == SessionStatus.CONNECTED
        assert result.phone_number == "5511999999999"


@pytest.mark.asyncio
async def test_fetch_session_status_pending(evolution_provider):
    """Test fetching session status when pending."""
    session_id = "tenant-test"

    with patch.object(evolution_provider, "_request_with_retry", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "instance": {
                "state": "PENDING",
            }
        }
        result = await evolution_provider.fetch_session_status(session_id)

        assert result.status == SessionStatus.PENDING
        assert result.phone_number is None


@pytest.mark.asyncio
async def test_stop_session(evolution_provider):
    """Test stopping a session."""
    session_id = "tenant-test"

    with patch.object(evolution_provider, "_request_with_retry", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {}
        await evolution_provider.stop_session(session_id)

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "DELETE"
        assert session_id in call_args[0][1]
        assert "/instance/logout/" in call_args[0][1]


@pytest.mark.asyncio
async def test_normalize_webhook_payload_message_upsert():
    """Test webhook payload normalization for MESSAGES_UPSERT event."""
    provider = EvolutionWhatsAppProvider()

    payload = {
        "event": "MESSAGES_UPSERT",
        "instance": "tenant-test",
        "data": {
            "messages": [
                {
                    "key": {
                        "id": "msg-123",
                        "remoteJid": "5511999999999@s.whatsapp.net",
                        "fromMe": False,
                    },
                    "message": {"conversation": "Hello"},
                    "messageTimestamp": 1686000000,
                    "pushName": "Test User",
                }
            ]
        },
    }

    result = provider.normalize_webhook_payload(payload)

    assert result is not None
    assert result.event_name == "message.upsert"
    assert result.session_id == "tenant-test"
    assert result.message_id == "msg-123"
    assert result.remote_jid == "5511999999999@s.whatsapp.net"
    assert result.push_name == "Test User"
    assert result.from_me is False
    assert result.timestamp_raw == 1686000000


@pytest.mark.asyncio
async def test_normalize_webhook_payload_ignored_event():
    """Test that non-message events are ignored."""
    provider = EvolutionWhatsAppProvider()

    payload = {
        "event": "CONNECTION_UPDATE",
        "instance": "tenant-test",
        "data": {"status": "OPEN"},
    }

    result = provider.normalize_webhook_payload(payload)
    assert result is None


@pytest.mark.asyncio
async def test_normalize_webhook_payload_missing_remote_jid():
    """Test that payloads without remoteJid are ignored."""
    provider = EvolutionWhatsAppProvider()

    payload = {
        "event": "MESSAGES_UPSERT",
        "instance": "tenant-test",
        "data": {
            "messages": [
                {
                    "key": {"id": "msg-123"},
                    "message": {"conversation": "Hello"},
                }
            ]
        },
    }

    result = provider.normalize_webhook_payload(payload)
    assert result is None


@pytest.mark.asyncio
async def test_normalize_webhook_payload_missing_instance():
    """Test that payloads without instance are ignored."""
    provider = EvolutionWhatsAppProvider()

    payload = {
        "event": "MESSAGES_UPSERT",
        "data": {
            "messages": [
                {
                    "key": {
                        "id": "msg-123",
                        "remoteJid": "5511999999999@s.whatsapp.net",
                    },
                    "message": {"conversation": "Hello"},
                }
            ]
        },
    }

    result = provider.normalize_webhook_payload(payload)
    assert result is None
