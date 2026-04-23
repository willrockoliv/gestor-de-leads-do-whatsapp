"""
Script para popular o banco Postgres do Docker Compose com tenant, usuário e lead de teste.
Roda fora do ambiente de testes/pytest, usando a mesma conexão do backend.
"""
import asyncio
from sqlalchemy import text
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.models import Tenant, User, Lead
from app.core.security import hash_password

async def seed():
    async with AsyncSessionLocal() as session:
        # Remove leads e usuários do tenant de teste
        await session.execute(text("DELETE FROM leads"))
        await session.execute(text("DELETE FROM users"))
        await session.execute(text("DELETE FROM tenants"))
        await session.commit()

        funnel_config = {"1": "Prospecção", "2": "Contato", "3": "Fechamento"}
        tenant = Tenant(name="Tenant Teste", funnel_config=funnel_config)
        session.add(tenant)
        await session.flush()
        user = User(
            tenant_id=tenant.id,
            email="teste@teste.com",
            hashed_password=hash_password("123456"),
        )
        session.add(user)
        lead = Lead(
            tenant_id=tenant.id,
            phone="11999999999",
            name="Lead Teste",
            current_stage="Prospecção",
            temperature_score=55,
        )
        session.add(lead)
        await session.commit()
        print("Seed inserida com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed())
