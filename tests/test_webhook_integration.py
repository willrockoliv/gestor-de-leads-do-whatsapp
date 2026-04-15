import uuid
import pytest
from sqlalchemy import select

from app.models import Tenant, Lead, Message, LeadStatus


def _make_webhook_payload(phone: str = "5511999999999", content: str = "Oi", from_me: bool = False, push_name: str = "João"):
    return {
        "event": "message.upsert",
        "instance": None,
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


@pytest.fixture
async def tenant_in_db(client):
    """Create a tenant via register endpoint and return token + tenant_id."""
    resp = await client.post("/auth/register", json={
        "email": f"webhook-{uuid.uuid4().hex[:8]}@test.com",
        "password": "senha123",
        "business_name": "Loja Webhook",
    })
    token = resp.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"token": token, "tenant_id": me.json()["tenant_id"]}


async def test_webhook_creates_new_lead(client, tenant_in_db):
    payload = _make_webhook_payload(phone="5511000000001", content="Quero saber o preço")
    resp = await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "message_id" in data


async def test_webhook_persists_message(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000002"
    payload = _make_webhook_payload(phone=phone, content="Boa tarde!")
    await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))

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

    # Create a converted lead directly
    async with AsyncSessionTest() as session:
        lead = Lead(tenant_id=tid, phone=phone, status=LeadStatus.converted, is_processing=False)
        session.add(lead)
        await session.commit()

    payload = _make_webhook_payload(phone=phone, content="Oi")
    resp = await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))
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

    payload = _make_webhook_payload(phone=phone, content="Oi")
    resp = await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discarded"


async def test_webhook_outbound_message(client, tenant_in_db):
    from tests.conftest import AsyncSessionTest

    phone = "5511000000005"
    payload = _make_webhook_payload(phone=phone, content="Olá!", from_me=True)
    resp = await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))
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
        payload = _make_webhook_payload(phone=phone, content=text)
        await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.phone == phone))
        lead = result.scalar_one()
        result = await session.execute(select(Message).where(Message.lead_id == lead.id))
        messages = result.scalars().all()
        assert len(messages) == 3


async def test_webhook_ignores_non_message_event(client, tenant_in_db):
    payload = {
        "event": "connection.update",
        "instance": None,
        "data": {
            "key": {"remoteJid": "5511@s.whatsapp.net", "fromMe": False, "id": "X"},
            "message": None,
            "pushName": None,
            "messageTimestamp": None,
        },
    }
    resp = await client.post("/webhooks/whatsapp", content=__import__("json").dumps(payload))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"
