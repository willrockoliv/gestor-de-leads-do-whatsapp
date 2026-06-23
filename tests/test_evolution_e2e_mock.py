"""Integration tests for Evolution API WhatsApp provider with mock HTTP server."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.whatsapp.evolution import EvolutionWhatsAppProvider
from app.providers.whatsapp.interface import (
    ProviderSessionStatus,
    WhatsAppProviderAlreadyExistsError,
    WhatsAppProviderError,
)
from app.models import SessionStatus


@pytest.fixture
def evolution_provider_with_config():
    """Create Evolution provider with test configuration."""
    with patch("app.providers.whatsapp.evolution.get_settings") as mock_settings:
        mock_settings.return_value.EVOLUTION_API_URL = "http://evolution-api:8080"
        mock_settings.return_value.EVOLUTION_API_KEY = "test-api-key"
        mock_settings.return_value.WEBHOOK_URL = "http://localhost:8000/webhooks/whatsapp"
        provider = EvolutionWhatsAppProvider()
    return provider


@pytest.mark.asyncio
async def test_evolution_full_connection_flow(evolution_provider_with_config):
    """Test complete Evolution API connection flow."""
    provider = evolution_provider_with_config
    tenant_id = uuid4()
    session_id = f"tenant-{tenant_id}"
    mock_db = AsyncMock(spec=AsyncSession)

    # Simulate sequence:
    # 1. Create session
    # 2. Fetch QR code
    # 3. Check status progression (PENDING -> QR_CODE_READY -> CONNECTING -> CONNECTED)
    # 4. Get phone number
    # 5. Stop session

    call_sequence = []

    async def mock_request(method, url, **kwargs):
        call_sequence.append((method, url))

        if method == "POST" and "/instance/create" in url:
            return {"instanceId": session_id}
        elif method == "GET" and "/instance/connect/" in url:
            return {"qr": "base64_qr_code_data"}
        elif method == "GET" and "/instance/connectionState/" in url:
            # Simulate status progression
            if len([c for c in call_sequence if "/instance/connectionState/" in c[1]]) == 1:
                return {"instance": {"state": "PENDING"}}
            elif len([c for c in call_sequence if "/instance/connectionState/" in c[1]]) == 2:
                return {"instance": {"state": "QR_CODE_READY"}}
            elif len([c for c in call_sequence if "/instance/connectionState/" in c[1]]) == 3:
                return {"instance": {"state": "CONNECTING"}}
            else:
                return {"instance": {"state": "OPEN", "phoneNumber": "5511999999999"}}
        elif method == "DELETE" and "/instance/logout/" in url:
            return {}

        return {}

    with patch.object(provider, "_request_with_retry", side_effect=mock_request):
        # 1. Create session
        await provider.create_session(mock_db, tenant_id, session_id)
        assert len(call_sequence) == 1
        assert call_sequence[0] == ("POST", f"{provider.base_url}/instance/create")

        # 2. Fetch QR code
        qr_code = await provider.fetch_qr_code(session_id)
        assert qr_code == "base64_qr_code_data"
        assert len(call_sequence) == 2

        # 3. Check status progression
        status1 = await provider.fetch_session_status(session_id)
        assert status1.status == SessionStatus.PENDING
        assert status1.phone_number is None

        status2 = await provider.fetch_session_status(session_id)
        assert status2.status == SessionStatus.QR_CODE_READY

        status3 = await provider.fetch_session_status(session_id)
        assert status3.status == SessionStatus.CONNECTING

        status4 = await provider.fetch_session_status(session_id)
        assert status4.status == SessionStatus.CONNECTED
        assert status4.phone_number == "5511999999999"

        # 4. Stop session
        await provider.stop_session(session_id)
        assert call_sequence[-1] == ("DELETE", f"{provider.base_url}/instance/logout/{session_id}")


@pytest.mark.asyncio
async def test_evolution_webhook_message_upsert_normalization(evolution_provider_with_config):
    """Test webhook payload normalization for complete message flow."""
    provider = evolution_provider_with_config

    # Simulate a complete webhook from Evolution
    webhook_payload = {
        "event": "MESSAGES_UPSERT",
        "instance": "tenant-test-123",
        "data": {
            "messages": [
                {
                    "key": {
                        "remoteJid": "5511987654321@s.whatsapp.net",
                        "id": "3EB0045E7F57D1D36E",
                        "fromMe": False,
                    },
                    "message": {
                        "conversation": "Oi, estou interessado no produto",
                        "extendedTextMessage": {
                            "text": "Oi, estou interessado no produto",
                        },
                    },
                    "messageTimestamp": 1686048000,
                    "pushName": "João Silva",
                    "broadcast": False,
                    "status": "PENDING",
                }
            ]
        },
    }

    normalized = provider.normalize_webhook_payload(webhook_payload)

    assert normalized is not None
    assert normalized.event_name == "message.upsert"
    assert normalized.session_id == "tenant-test-123"
    assert normalized.message_id == "3EB0045E7F57D1D36E"
    assert normalized.remote_jid == "5511987654321@s.whatsapp.net"
    assert normalized.push_name == "João Silva"
    assert normalized.from_me is False
    assert normalized.timestamp_raw == 1686048000


@pytest.mark.asyncio
async def test_evolution_webhook_media_message_normalization(evolution_provider_with_config):
    """Test normalization of media messages."""
    provider = evolution_provider_with_config

    webhook_payload = {
        "event": "MESSAGES_UPSERT",
        "instance": "tenant-test-456",
        "data": {
            "messages": [
                {
                    "key": {
                        "remoteJid": "5511999999999@s.whatsapp.net",
                        "id": "MEDIA001",
                        "fromMe": False,
                    },
                    "message": {
                        "imageMessage": {
                            "url": "https://example.com/image.jpg",
                            "caption": "Check this out",
                        }
                    },
                    "messageTimestamp": 1686048000,
                    "pushName": "Sender Name",
                }
            ]
        },
    }

    normalized = provider.normalize_webhook_payload(webhook_payload)

    assert normalized is not None
    assert normalized.event_name == "message.upsert"
    assert normalized.remote_jid == "5511999999999@s.whatsapp.net"
    assert "imageMessage" in normalized.content_payload


@pytest.mark.asyncio
async def test_evolution_multi_tenant_sessions(evolution_provider_with_config):
    """Test that multiple tenants can have separate sessions."""
    provider = evolution_provider_with_config
    mock_db = AsyncMock(spec=AsyncSession)

    tenant_1_id = uuid4()
    tenant_2_id = uuid4()

    session_1_id = await provider.resolve_session_id(tenant_1_id)
    session_2_id = await provider.resolve_session_id(tenant_2_id)

    # Sessions should be different
    assert session_1_id != session_2_id
    assert str(tenant_1_id) in session_1_id
    assert str(tenant_2_id) in session_2_id

    # Simulate creating both sessions
    async def mock_request(method, url, **kwargs):
        if method == "POST" and "/instance/create" in url:
            return {"instanceId": kwargs.get("json_payload", {}).get("instanceName")}
        return {}

    with patch.object(provider, "_request_with_retry", side_effect=mock_request):
        await provider.create_session(mock_db, tenant_1_id, session_1_id)
        await provider.create_session(mock_db, tenant_2_id, session_2_id)


@pytest.mark.asyncio
async def test_evolution_error_handling_conflict(evolution_provider_with_config):
    """Test proper error handling for session conflicts."""
    provider = evolution_provider_with_config
    mock_db = AsyncMock(spec=AsyncSession)
    tenant_id = uuid4()
    session_id = f"tenant-{tenant_id}"

    # Mock conflict response (409)
    async def mock_conflict_request(method, url, **kwargs):
        raise WhatsAppProviderAlreadyExistsError("Instance already exists")

    with patch.object(provider, "_request_with_retry", side_effect=mock_conflict_request):
        with pytest.raises(WhatsAppProviderAlreadyExistsError):
            await provider.create_session(mock_db, tenant_id, session_id)


@pytest.mark.asyncio
async def test_evolution_status_mapping_all_states(evolution_provider_with_config):
    """Test all Evolution API status mappings."""
    provider = evolution_provider_with_config

    status_mappings = [
        ("PENDING", SessionStatus.PENDING),
        ("QR_CODE_READY", SessionStatus.QR_CODE_READY),
        ("CONNECTING", SessionStatus.CONNECTING),
        ("OPEN", SessionStatus.CONNECTED),
        ("CONNECTED", SessionStatus.CONNECTED),
        ("CLOSED", SessionStatus.DISCONNECTED),
        ("DISCONNECTED", SessionStatus.DISCONNECTED),
        ("UNKNOWN_STATUS", SessionStatus.ERROR),
    ]

    async def mock_request_with_status(status):
        async def mock_request(method, url, **kwargs):
            return {"instance": {"state": status}}

        return mock_request

    for evolution_status, expected_internal_status in status_mappings:
        mock_request = await mock_request_with_status(evolution_status)
        with patch.object(provider, "_request_with_retry", side_effect=mock_request):
            result = await provider.fetch_session_status("test-session")
            assert result.status == expected_internal_status


@pytest.mark.asyncio
async def test_evolution_webhook_multiple_messages_first_only(evolution_provider_with_config):
    """Test that only first message in batch is processed."""
    provider = evolution_provider_with_config

    webhook_payload = {
        "event": "MESSAGES_UPSERT",
        "instance": "tenant-test",
        "data": {
            "messages": [
                {
                    "key": {
                        "remoteJid": "5511999999999@s.whatsapp.net",
                        "id": "msg-first",
                        "fromMe": False,
                    },
                    "message": {"conversation": "First message"},
                    "messageTimestamp": 1686048000,
                    "pushName": "User",
                },
                {
                    "key": {
                        "remoteJid": "5511999999999@s.whatsapp.net",
                        "id": "msg-second",
                        "fromMe": False,
                    },
                    "message": {"conversation": "Second message"},
                    "messageTimestamp": 1686048001,
                    "pushName": "User",
                },
            ]
        },
    }

    normalized = provider.normalize_webhook_payload(webhook_payload)

    # Should only process first message
    assert normalized.message_id == "msg-first"


@pytest.mark.asyncio
async def test_evolution_webhook_messages_update_event(evolution_provider_with_config):
    """Test MESSAGES_UPDATE event is also handled."""
    provider = evolution_provider_with_config

    webhook_payload = {
        "event": "MESSAGES_UPDATE",
        "instance": "tenant-test",
        "data": {
            "messages": [
                {
                    "key": {
                        "remoteJid": "5511999999999@s.whatsapp.net",
                        "id": "msg-123",
                        "fromMe": False,
                    },
                    "message": {"conversation": "Updated message"},
                    "messageTimestamp": 1686048000,
                    "pushName": "User",
                }
            ]
        },
    }

    normalized = provider.normalize_webhook_payload(webhook_payload)

    assert normalized is not None
    assert normalized.event_name == "message.upsert"  # Both map to same internal event


@pytest.mark.asyncio
async def test_evolution_phone_number_normalization(evolution_provider_with_config):
    """Test phone number normalization."""
    provider = evolution_provider_with_config

    async def mock_request(method, url, **kwargs):
        return {
            "instance": {
                "state": "OPEN",
                "phoneNumber": "+5511987654321",
            }
        }

    with patch.object(provider, "_request_with_retry", side_effect=mock_request):
        result = await provider.fetch_session_status("test-session")

        # Should strip leading +
        assert result.phone_number == "5511987654321"
