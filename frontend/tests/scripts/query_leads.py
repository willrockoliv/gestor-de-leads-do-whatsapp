import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.models import Analysis, Lead, Message


async def main():
    async with AsyncSessionLocal() as session:
        leads = (await session.execute(select(Lead))).scalars().all()
        print(f'Leads: {len(leads)}')
        for lead in leads:
            print(f'Lead: {lead.id}, {lead.name}, {lead.status}, {lead.current_stage}, {lead.temperature_score}')
            msgs = (await session.execute(select(Message).where(Message.lead_id==lead.id))).scalars().all()
            print(f'  Messages: {len(msgs)}')
            for msg in msgs:
                print(f'    {msg.direction}: {msg.content}')
            analyses = (await session.execute(select(Analysis).where(Analysis.lead_id==lead.id))).scalars().all()
            print(f'  Analyses: {len(analyses)}')
            for a in analyses:
                print(f'    Score: {a.temperature_score}, Stage: {a.current_stage}')

if __name__ == "__main__":
    asyncio.run(main())
