import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Lead, Message, Analysis, MessageDirection

async def main():
    async with AsyncSessionLocal() as session:
        lead = (await session.execute(select(Lead))).scalars().first()
        if not lead:
            print('Nenhum lead encontrado.')
            return
        # Mensagens
        msg1 = Message(lead_id=lead.id, direction=MessageDirection.inbound, content="Olá, gostaria de saber mais!")
        msg2 = Message(lead_id=lead.id, direction=MessageDirection.outbound, content="Claro! Posso ajudar sim.")
        session.add_all([msg1, msg2])
        # Análise
        analysis = Analysis(
            lead_id=lead.id,
            temperature_score=lead.temperature_score or 55,
            current_stage=lead.current_stage,
            conversation_summary="Lead interessado, respondeu rápido.",
            qualitative_tips="Responder em até 5 minutos aumenta conversão.",
            suggested_reply="Vamos marcar uma call?",
        )
        session.add(analysis)
        await session.commit()
        print('Mensagens e análise inseridas!')

if __name__ == "__main__":
    asyncio.run(main())
