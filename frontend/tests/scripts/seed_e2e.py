"""
Script para popular o banco Postgres do Docker Compose com tenant, usuário e lead de teste.
Roda fora do ambiente de testes/pytest, usando a mesma conexão do backend.
"""
import asyncio

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.models import Lead, Tenant, User


async def seed():
    async with AsyncSessionLocal() as session:
        # Remove na ordem correta para respeitar FKs
        await session.execute(text("DELETE FROM messages"))
        await session.execute(text("DELETE FROM analyses"))
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
        # Lead Quente
        lead_quente = Lead(
            tenant_id=tenant.id,
            phone="11999999999",
            name="Lead Quente",
            current_stage="Prospecção",
            temperature_score=80,
        )
        # Lead Morno
        lead_morno = Lead(
            tenant_id=tenant.id,
            phone="11988888888",
            name="Lead Morno",
            current_stage="Contato",
            temperature_score=55,
        )
        # Lead Frio
        lead_frio = Lead(
            tenant_id=tenant.id,
            phone="11977777777",
            name="Lead Frio",
            current_stage="Fechamento",
            temperature_score=20,
        )
        session.add_all([lead_quente, lead_morno, lead_frio])
        await session.flush()

        # Mensagens para cada lead
        from app.models.models import Message, MessageDirection
        messages = [
            Message(lead_id=lead_quente.id, direction=MessageDirection.inbound, content="Olá, quero saber mais sobre o produto!"),
            Message(lead_id=lead_quente.id, direction=MessageDirection.outbound, content="Claro! Posso te ajudar com as informações."),
            Message(lead_id=lead_morno.id, direction=MessageDirection.inbound, content="Oi, estou pensando em comprar."),
            Message(lead_id=lead_frio.id, direction=MessageDirection.inbound, content="Só olhando, obrigado."),
        ]
        session.add_all(messages)
        await session.commit()
        print("Seed inserida com sucesso! (quente, morno, frio, com mensagens)")

if __name__ == "__main__":
    asyncio.run(seed())
