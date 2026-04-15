import uuid
import pytest
from sqlalchemy import select

from app.models import Tenant, User, Lead, Message, Analysis, LeadStatus, MessageDirection


async def test_tenant_persist(client):
    """Test that a Tenant can be persisted and queried."""
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.uuid4()
    async with AsyncSessionTest() as session:
        tenant = Tenant(id=tenant_id, name="Minha Loja", funnel_config={"etapa_1": "Descoberta"})
        session.add(tenant)
        await session.commit()

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        t = result.scalar_one()
        assert t.name == "Minha Loja"
        assert t.funnel_config == {"etapa_1": "Descoberta"}


async def test_user_tenant_relationship(client):
    """Test User -> Tenant FK relationship."""
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with AsyncSessionTest() as session:
        tenant = Tenant(id=tenant_id, name="Loja FK")
        session.add(tenant)
        await session.flush()

        user = User(id=user_id, tenant_id=tenant_id, email="fk@test.com", hashed_password="hash")
        session.add(user)
        await session.commit()

    async with AsyncSessionTest() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        u = result.scalar_one()
        assert u.tenant_id == tenant_id


async def test_lead_messages_relationship(client):
    """Test Lead -> Messages one-to-many relationship."""
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.uuid4()
    lead_id = uuid.uuid4()

    async with AsyncSessionTest() as session:
        tenant = Tenant(id=tenant_id, name="Loja Msgs")
        session.add(tenant)
        await session.flush()

        lead = Lead(id=lead_id, tenant_id=tenant_id, phone="5511999990000")
        session.add(lead)
        await session.flush()

        msg1 = Message(lead_id=lead_id, direction=MessageDirection.inbound, content="Oi")
        msg2 = Message(lead_id=lead_id, direction=MessageDirection.outbound, content="Olá!")
        session.add_all([msg1, msg2])
        await session.commit()

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Message).where(Message.lead_id == lead_id))
        messages = result.scalars().all()
        assert len(messages) == 2


async def test_lead_analysis_relationship(client):
    """Test Lead -> Analysis relationship."""
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.uuid4()
    lead_id = uuid.uuid4()

    async with AsyncSessionTest() as session:
        tenant = Tenant(id=tenant_id, name="Loja Analysis")
        session.add(tenant)
        await session.flush()

        lead = Lead(id=lead_id, tenant_id=tenant_id, phone="5511999991111")
        session.add(lead)
        await session.flush()

        analysis = Analysis(
            lead_id=lead_id,
            temperature_score=80,
            current_stage="Descoberta",
            conversation_summary="Resumo",
            qualitative_tips="Dicas",
            suggested_reply="Resposta",
        )
        session.add(analysis)
        await session.commit()

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Analysis).where(Analysis.lead_id == lead_id))
        a = result.scalar_one()
        assert a.temperature_score == 80
        assert a.conversation_summary == "Resumo"


async def test_lead_db_defaults(client):
    """Test that Lead defaults (status, is_processing) are applied at INSERT."""
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.uuid4()
    lead_id = uuid.uuid4()

    async with AsyncSessionTest() as session:
        tenant = Tenant(id=tenant_id, name="Loja Defaults")
        session.add(tenant)
        await session.flush()

        lead = Lead(id=lead_id, tenant_id=tenant_id, phone="5511777770000")
        session.add(lead)
        await session.commit()

    async with AsyncSessionTest() as session:
        result = await session.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one()
        assert lead.status == LeadStatus.active
        assert lead.is_processing is False
        assert lead.temperature_score is None
