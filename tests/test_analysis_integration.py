import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select, update

from app.models import Analysis, Lead, LeadStatus, Message, MessageDirection

MOCK_LLM_RESPONSE = json.dumps({
    "temperature_score": 80,
    "current_stage": "Descoberta",
    "conversation_summary": "Cliente interessado no produto",
    "qualitative_tips": "Lead quente, fechar rápido",
    "suggested_reply": "Vamos agendar uma call?",
})


@pytest.fixture
async def setup_lead(client):
    """Register user, create lead with messages, return token + lead_id."""
    from tests.conftest import AsyncSessionTest

    resp = await client.post("/auth/register", json={
        "email": f"analysis-{uuid.uuid4().hex[:8]}@test.com",
        "password": "senha123",
        "business_name": "Loja Analysis",
    })
    token = resp.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    tenant_id = uuid.UUID(me.json()["tenant_id"])

    lead_id = uuid.uuid4()
    async with AsyncSessionTest() as session:
        lead = Lead(id=lead_id, tenant_id=tenant_id, phone="5511111111111", status=LeadStatus.active, is_processing=False)
        session.add(lead)
        await session.flush()

        session.add(Message(lead_id=lead_id, direction=MessageDirection.inbound, content="Oi, quero saber o preço"))
        session.add(Message(lead_id=lead_id, direction=MessageDirection.outbound, content="Olá! R$100"))
        session.add(Message(lead_id=lead_id, direction=MessageDirection.inbound, content="Tem desconto?"))
        await session.commit()

    return {"token": token, "lead_id": str(lead_id), "tenant_id": str(tenant_id)}


async def test_analyze_single_lead(client, setup_lead):
    token = setup_lead["token"]
    lead_id = setup_lead["lead_id"]

    with patch("app.services.analysis_service.call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE):
        resp = await client.post(
            f"/leads/{lead_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["temperature_score"] == 80
    assert data["current_stage"] == "Descoberta"
    assert data["conversation_summary"] == "Cliente interessado no produto"
    assert data["suggested_reply"] == "Vamos agendar uma call?"


async def test_analyze_double_submit_409(client, setup_lead):
    """Test that submitting analyze while already processing returns 409."""
    from tests.conftest import AsyncSessionTest

    token = setup_lead["token"]
    lead_id = setup_lead["lead_id"]

    # Manually set is_processing = True
    async with AsyncSessionTest() as session:
        await session.execute(
            update(Lead).where(Lead.id == uuid.UUID(lead_id)).values(
                is_processing=True,
                processing_started_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    resp = await client.post(
        f"/leads/{lead_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_analyze_lead_not_found(client, setup_lead):
    token = setup_lead["token"]
    fake_id = str(uuid.uuid4())

    resp = await client.post(
        f"/leads/{fake_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_analyze_updates_lead_score(client, setup_lead):
    from tests.conftest import AsyncSessionTest

    token = setup_lead["token"]
    lead_id = setup_lead["lead_id"]

    with patch("app.services.analysis_service.call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE):
        await client.post(
            f"/leads/{lead_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.id == uuid.UUID(lead_id)))
        lead = result.scalar_one()
        assert lead.temperature_score == 80
        assert lead.current_stage == "Descoberta"
        assert lead.is_processing is False  # Lock released


async def test_analyze_releases_lock_on_error(client, setup_lead):
    from tests.conftest import AsyncSessionTest

    token = setup_lead["token"]
    lead_id = setup_lead["lead_id"]

    with patch("app.services.analysis_service.call_llm", new_callable=AsyncMock, side_effect=Exception("LLM timeout")):
        resp = await client.post(
            f"/leads/{lead_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 500

    # Lock should be released
    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.id == uuid.UUID(lead_id)))
        lead = result.scalar_one()
        assert lead.is_processing is False


async def test_zombie_lock_reset(client, setup_lead):
    from app.services.analysis_service import reset_zombie_locks
    from tests.conftest import AsyncSessionTest

    lead_id = uuid.UUID(setup_lead["lead_id"])

    # Set a zombie lock (processing started 10 min ago)
    async with AsyncSessionTest() as session:
        await session.execute(
            update(Lead).where(Lead.id == lead_id).values(
                is_processing=True,
                processing_started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            )
        )
        await session.commit()

    # Run watchdog
    async with AsyncSessionTest() as session:
        count = await reset_zombie_locks(session, timeout_minutes=5)
        assert count == 1

    # Verify lock released
    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one()
        assert lead.is_processing is False


async def test_zombie_lock_skip_recent(client, setup_lead):
    from app.services.analysis_service import reset_zombie_locks
    from tests.conftest import AsyncSessionTest

    lead_id = uuid.UUID(setup_lead["lead_id"])

    # Set a recent lock (2 min ago — should NOT be reset)
    async with AsyncSessionTest() as session:
        await session.execute(
            update(Lead).where(Lead.id == lead_id).values(
                is_processing=True,
                processing_started_at=datetime.now(timezone.utc) - timedelta(minutes=2),
            )
        )
        await session.commit()

    async with AsyncSessionTest() as session:
        count = await reset_zombie_locks(session, timeout_minutes=5)
        assert count == 0


async def test_analyze_persists_analysis(client, setup_lead):
    from tests.conftest import AsyncSessionTest

    token = setup_lead["token"]
    lead_id = setup_lead["lead_id"]

    with patch("app.services.analysis_service.call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE):
        await client.post(
            f"/leads/{lead_id}/analyze",
            headers={"Authorization": f"Bearer {token}"},
        )

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Analysis).where(Analysis.lead_id == uuid.UUID(lead_id)))
        analysis = result.scalar_one()
        assert analysis.temperature_score == 80
        assert analysis.conversation_summary == "Cliente interessado no produto"
