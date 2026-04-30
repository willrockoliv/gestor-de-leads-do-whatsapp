import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Tenant, Lead

async def main():
    async with AsyncSessionLocal() as session:
        # Busca o primeiro tenant existente usando ORM
        tenant = await session.scalar(select(Tenant).limit(1))
        if tenant is None:
            # Cria tenant se não existir
            tenant = Tenant(name="Tenant Seed", funnel_config={"1": "Prospecção", "2": "Contato", "3": "Fechamento"})
            session.add(tenant)
            await session.flush()
        # Cria lead com temperature_score 80
        lead = Lead(
            tenant_id=tenant.id,
            phone="11988887777",
            name="Lead Quente",
            current_stage="Prospecção",
            temperature_score=80,
        )
        session.add(lead)
        await session.commit()
        print(f"Lead quente criado: {lead.id}")

if __name__ == "__main__":
    asyncio.run(main())
