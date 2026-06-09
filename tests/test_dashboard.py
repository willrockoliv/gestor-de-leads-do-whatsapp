import uuid

import pytest
from sqlalchemy import select

from app.models import Analysis, Lead, LeadStatus, Message, MessageDirection


@pytest.fixture
async def auth_with_leads(client):
    """Register user and create several leads with messages for testing."""
    from tests.conftest import AsyncSessionTest

    resp = await client.post("/auth/register", json={
        "email": f"dash-{uuid.uuid4().hex[:8]}@test.com",
        "password": "senha123",
        "business_name": "Loja Dashboard",
    })
    token = resp.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    tenant_id = uuid.UUID(me.json()["tenant_id"])

    lead_ids = []
    async with AsyncSessionTest() as session:
        # Lead 1: active, high score
        lid1 = uuid.uuid4()
        session.add(Lead(id=lid1, tenant_id=tenant_id, phone="5511000001", name="João",
                         status=LeadStatus.active, is_processing=False,
                         current_stage="Descoberta", temperature_score=90))
        session.add(Message(lead_id=lid1, direction=MessageDirection.inbound, content="Oi"))
        session.add(Message(lead_id=lid1, direction=MessageDirection.outbound, content="Olá!"))
        session.add(Analysis(lead_id=lid1, temperature_score=90, current_stage="Descoberta",
                             conversation_summary="Resumo 1", qualitative_tips="Tip 1",
                             suggested_reply="Reply 1"))
        lead_ids.append(lid1)

        # Lead 2: active, low score
        lid2 = uuid.uuid4()
        session.add(Lead(id=lid2, tenant_id=tenant_id, phone="5511000002", name="Maria",
                         status=LeadStatus.active, is_processing=False,
                         current_stage="Orçamento Enviado", temperature_score=30))
        session.add(Message(lead_id=lid2, direction=MessageDirection.inbound, content="Preço?"))
        lead_ids.append(lid2)

        # Lead 3: converted
        lid3 = uuid.uuid4()
        session.add(Lead(id=lid3, tenant_id=tenant_id, phone="5511000003", name="Pedro",
                         status=LeadStatus.converted, is_processing=False,
                         temperature_score=100))
        lead_ids.append(lid3)

        # Lead 4: lost
        lid4 = uuid.uuid4()
        session.add(Lead(id=lid4, tenant_id=tenant_id, phone="5511000004", name="Ana",
                         status=LeadStatus.lost, is_processing=False))
        lead_ids.append(lid4)

        await session.commit()

    return {"token": token, "tenant_id": str(tenant_id), "lead_ids": [str(lid) for lid in lead_ids]}


# --- GET /leads ---

async def test_list_leads_default(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/leads", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # Default: only active leads
    assert len(data) == 2
    # Sorted by temperature desc
    assert data[0]["temperature_score"] >= data[1]["temperature_score"]


async def test_list_leads_filter_by_stage(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/leads?stage=Descoberta", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["current_stage"] == "Descoberta"


async def test_list_leads_filter_by_score(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/leads?min_score=50", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["temperature_score"] >= 50 for item in data)


async def test_list_leads_sort_asc(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/leads?order=asc", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    scores = [d["temperature_score"] for d in data if d["temperature_score"] is not None]
    assert scores == sorted(scores)


async def test_list_leads_conversation_time(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/leads", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    # Lead 1 has 2 messages, should have conversation time
    lead1 = next(d for d in data if d["name"] == "João")
    assert lead1["conversation_time_minutes"] is not None


# --- GET /leads/{id} ---

async def test_get_lead_detail(client, auth_with_leads):
    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][0]
    resp = await client.get(f"/leads/{lead_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "João"
    assert data["latest_analysis"] is not None
    assert data["latest_analysis"]["temperature_score"] == 90
    assert data["latest_analysis"]["conversation_summary"] == "Resumo 1"


async def test_get_lead_not_found(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get(f"/leads/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


async def test_get_lead_without_analysis(client, auth_with_leads):
    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][1]  # Lead 2, no analysis
    resp = await client.get(f"/leads/{lead_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["latest_analysis"] is None


# --- GET /leads/{id}/messages ---

async def test_get_messages(client, auth_with_leads):
    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][0]
    resp = await client.get(f"/leads/{lead_id}/messages", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["direction"] in ("inbound", "outbound")


async def test_get_messages_not_found(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get(f"/leads/{uuid.uuid4()}/messages", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# --- PATCH /leads/{id}/status ---

async def test_update_lead_to_converted(client, auth_with_leads):
    from tests.conftest import AsyncSessionTest

    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][0]

    resp = await client.patch(
        f"/leads/{lead_id}/status",
        json={"status": "converted"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "converted"

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.id == uuid.UUID(lead_id)))
        lead = result.scalar_one()
        assert lead.status == LeadStatus.converted


async def test_update_lead_to_lost(client, auth_with_leads):
    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][1]

    resp = await client.patch(
        f"/leads/{lead_id}/status",
        json={"status": "lost"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "lost"


async def test_update_lead_invalid_status(client, auth_with_leads):
    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][0]

    resp = await client.patch(
        f"/leads/{lead_id}/status",
        json={"status": "invalid"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# --- PATCH /leads/{id}/stage ---

async def test_update_lead_stage(client, auth_with_leads):
    token = auth_with_leads["token"]
    lead_id = auth_with_leads["lead_ids"][0]

    resp = await client.patch(
        f"/leads/{lead_id}/stage",
        json={"current_stage": "Em Negociação"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_stage"] == "Em Negociação"


# --- GET /dashboard/stats ---

async def test_dashboard_stats(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_active"] == 2
    assert data["total_converted"] == 1
    assert data["total_lost"] == 1
    assert data["avg_temperature"] is not None
    assert "Descoberta" in data["leads_by_stage"]


# --- GET /whatsapp/status ---

async def test_whatsapp_status_no_session(client, auth_with_leads):
    token = auth_with_leads["token"]
    resp = await client.get("/whatsapp/status", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "DISCONNECTED"
