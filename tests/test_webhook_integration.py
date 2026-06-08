import hashlib
import hmac
import json
import uuid

import pytest
from sqlalchemy import select

from app.models import Lead, LeadStatus, Message, SessionStatus, WhatsAppSession


def _make_webhook_payload(
    session_id: str,
    phone: str = "5511999999999",
    content: str = "Oi",
    from_me: bool = False,
    push_name: str = "João",
):
    return {
        "event": "message.upsert",
        "session": session_id,
        "data": {
            "key": {
                "remoteJid": f"{phone}@s.whatsapp.net",
                "fromMe": from_me,
                "id": "ABC123",
            },
            "message": {"conversation": content},
            "pushName": push_name,
            "messageTimestamp": 1700000000,
        },
    }


def _signed_headers(payload: dict, secret: str) -> dict[str, str]:
    body = json.dumps(payload).encode()
    digest = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    return {
        "X-Webhook-Hmac": digest,
        "X-Webhook-Hmac-Algorithm": "sha512",
        "Content-Type": "application/json",
    }


@pytest.fixture
async def tenant_in_db(client):
    from tests.conftest import AsyncSessionTest

    resp = await client.post("/auth/register", json={
        "email": f"webhook-{uuid.uuid4().hex[:8]}@test.com",
        "password": "senha123",
        "business_name": "Loja Webhook",
    })
    token = resp.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    tenant_id = uuid.UUID(me.json()["tenant_id"])
    session_id = f"tenant-{tenant_id}"

    async with AsyncSessionTest() as session:
        wa_session = WhatsAppSession(
            tenant_id=tenant_id,
            session_id=session_id,
            status=SessionStatus.DISCONNECTED,
        )
        session.add(wa_session)
        await session.commit()

    return {"token": token, "tenant_id": me.json()["tenant_id"], "session_id": session_id}


async def test_webhook_creates_new_lead(client, tenant_in_db):
    payload = _make_webhook_payload(
        session_id=tenant_in_db["session_id"],
        phone="5511000000001",
        content="Quero saber o preço",
    )
    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "message_id" in data


async def test_webhook_persists_message(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000002"
    payload = _make_webhook_payload(session_id=tenant_in_db["session_id"], phone=phone, content="Boa tarde!")
    await client.post("/webhooks/whatsapp", content=json.dumps(payload))

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.phone == phone))
        lead = result.scalar_one()
        assert lead.name == "João"
        assert lead.status == LeadStatus.active

        result = await session.execute(select(Message).where(Message.lead_id == lead.id))
        msg = result.scalar_one()
        assert msg.content == "Boa tarde!"
        assert msg.direction.value == "inbound"


async def test_webhook_discards_converted_lead(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000003"
    tid = uuid.UUID(tenant_in_db["tenant_id"])

    async with AsyncSessionTest() as session:
        lead = Lead(tenant_id=tid, phone=phone, status=LeadStatus.converted, is_processing=False)
        session.add(lead)
        await session.commit()

    payload = _make_webhook_payload(session_id=tenant_in_db["session_id"], phone=phone, content="Oi")
    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discarded"


async def test_webhook_discards_lost_lead(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000004"
    tid = uuid.UUID(tenant_in_db["tenant_id"])

    async with AsyncSessionTest() as session:
        lead = Lead(tenant_id=tid, phone=phone, status=LeadStatus.lost, is_processing=False)
        session.add(lead)
        await session.commit()

    payload = _make_webhook_payload(session_id=tenant_in_db["session_id"], phone=phone, content="Oi")
    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discarded"


async def test_webhook_outbound_message(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000005"
    payload = _make_webhook_payload(session_id=tenant_in_db["session_id"], phone=phone, content="Olá!", from_me=True)
    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    assert resp.status_code == 200

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.phone == phone))
        lead = result.scalar_one()
        result = await session.execute(select(Message).where(Message.lead_id == lead.id))
        msg = result.scalar_one()
        assert msg.direction.value == "outbound"


async def test_webhook_multiple_messages_same_lead(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000006"
    for text in ["Msg 1", "Msg 2", "Msg 3"]:
        payload = _make_webhook_payload(session_id=tenant_in_db["session_id"], phone=phone, content=text)
        await client.post("/webhooks/whatsapp", content=json.dumps(payload))

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.phone == phone))
        lead = result.scalar_one()
        result = await session.execute(select(Message).where(Message.lead_id == lead.id))
        messages = result.scalars().all()
        assert len(messages) == 3


async def test_webhook_ignores_non_message_event(client, tenant_in_db):
    payload = {
        "event": "connection.update",
        "session": tenant_in_db["session_id"],
        "data": {
            "key": {"remoteJid": "5511@s.whatsapp.net", "fromMe": False, "id": "X"},
            "message": None,
            "pushName": None,
            "messageTimestamp": None,
        },
    }
    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_webhook_invalid_hmac_signature_returns_403(client, tenant_in_db, monkeypatch):
    from app.routers import webhooks

    monkeypatch.setattr(webhooks.settings, "WHATSAPP_WEBHOOK_HMAC_KEY", "top-secret")

    payload = _make_webhook_payload(session_id=tenant_in_db["session_id"], phone="5511991111111")
    headers = _signed_headers(payload, secret="wrong-secret")

    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload), headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Invalid signature"


async def test_webhook_unknown_session_returns_403(client, tenant_in_db, monkeypatch):
    from app.routers import webhooks

    monkeypatch.setattr(webhooks.settings, "WHATSAPP_WEBHOOK_HMAC_KEY", "top-secret")

    payload = _make_webhook_payload(session_id="unknown-session", phone="5511992222222")
    headers = _signed_headers(payload, secret="top-secret")

    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload), headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Unknown session"


async def test_webhook_invalid_json_returns_400(client, tenant_in_db):
    resp = await client.post(
        "/webhooks/whatsapp",
        content="{invalid-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid JSON payload"


async def test_webhook_replay_same_payload_is_ignored(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000007"
    payload = _make_webhook_payload(
        session_id=tenant_in_db["session_id"],
        phone=phone,
        content="Mensagem com retry",
    )

    first = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    second = await client.post("/webhooks/whatsapp", content=json.dumps(payload))

    assert first.status_code == 200
    assert first.json()["status"] == "ok"
    assert second.status_code == 200
    assert second.json()["status"] == "ignored"
    assert second.json()["reason"] == "replay detected"

    async with AsyncSessionTest() as session:
        lead = (await session.execute(select(Lead).where(Lead.phone == phone))).scalar_one()
        msgs = (await session.execute(select(Message).where(Message.lead_id == lead.id))).scalars().all()
        assert len(msgs) == 1
