import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Lead, Tenant

async def main():
    async with AsyncSessionLocal() as session:
        lead = (await session.execute(select(Lead))).scalars().first()
        if not lead:
            print('Nenhum lead encontrado.')
            return
        tenant = (await session.execute(select(Tenant).where(Tenant.id==lead.tenant_id))).scalars().first()
        print(f'Lead current_stage: {lead.current_stage}')
        print(f'Tenant funnel_config: {tenant.funnel_config}')
        etapas = set(tenant.funnel_config.values())
        print(f'Etapas possíveis: {etapas}')
        if lead.current_stage not in etapas:
            print('ATENÇÃO: current_stage do lead não existe no funnel_config do tenant!')
        else:
            print('current_stage do lead está correto.')

if __name__ == "__main__":
    asyncio.run(main())
