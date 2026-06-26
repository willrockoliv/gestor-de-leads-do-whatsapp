import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.models import Lead, Tenant, User


@pytest.fixture
async def seed_tenant_user_lead(setup_database):
    """
    Cria um tenant, um usuário e um lead com current_stage presente no funnel_config.
    Usuário: teste@teste.com / 123456
    Lead: current_stage='Prospecção', phone='11999999999', name='Lead Teste'
    """
    from tests.conftest import AsyncSessionTest
    async with AsyncSessionTest() as session:
        session: AsyncSession
        # Cria tenant com funnel_config
        funnel_config = {"1": "Prospecção", "2": "Contato", "3": "Fechamento"}
        tenant = Tenant(name="Tenant Teste", funnel_config=funnel_config)
        session.add(tenant)
        await session.flush()
        # Cria usuário
        user = User(
            tenant_id=tenant.id,
            email="teste@teste.com",
            hashed_password=hash_password("123456"),
        )
        session.add(user)
        # Cria lead com current_stage existente no funnel_config
        lead = Lead(
            tenant_id=tenant.id,
            phone="11999999999",
            name="Lead Teste",
            current_stage="Prospecção",
            temperature_score=55,
        )
        session.add(lead)
        await session.commit()
        yield {
            "tenant": tenant,
            "user": user,
            "lead": lead,
        }
