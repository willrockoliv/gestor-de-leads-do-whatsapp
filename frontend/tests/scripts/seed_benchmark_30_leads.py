"""Seed de benchmark para analise IA com 30 leads reais.

Uso:
  PYTHONPATH=. python3 frontend/tests/scripts/seed_benchmark_30_leads.py

O script:
- garante um tenant/usuario de benchmark (benchmark@teste.com / 123456)
- remove leads/mensagens/analises anteriores desse tenant
- cria 30 leads ativos com historico de conversa realista
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.models import (
    Analysis,
    AnalysisStatus,
    Lead,
    LeadStatus,
    Message,
    MessageDirection,
    Tenant,
    User,
)

BENCHMARK_EMAIL = "benchmark@teste.com"
BENCHMARK_PASSWORD = "123456"
TENANT_NAME = "Tenant Benchmark IA"
TOTAL_LEADS = 30

FUNNEL_CONFIG = {
    "1": "Prospecção",
    "2": "Qualificação",
    "3": "Negociação",
    "4": "Fechamento",
}


def _conversation_template(idx: int) -> list[tuple[MessageDirection, str]]:
    base_price = 97 + (idx % 9) * 11
    urgency = [
        "preciso resolver isso hoje",
        "consigo avançar essa semana",
        "quero comparar com outra opção",
    ][idx % 3]

    return [
        (MessageDirection.inbound, f"Oi, vi seu serviço e tenho interesse no plano {idx + 1}."),
        (MessageDirection.outbound, "Perfeito. Posso te explicar como funciona e valores."),
        (MessageDirection.inbound, f"Qual o preço e o que está incluso? {urgency}."),
        (MessageDirection.outbound, f"Temos planos a partir de R${base_price} e suporte dedicado."),
        (MessageDirection.inbound, "Se fechar hoje tem condição melhor?"),
        (MessageDirection.outbound, "Consigo aplicar condição comercial e onboarding prioritário."),
        (MessageDirection.inbound, "Ótimo. Me manda os próximos passos para contratar."),
    ]


async def seed_benchmark() -> None:
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        tenant_result = await session.execute(
            select(Tenant).where(Tenant.name == TENANT_NAME)
        )
        tenant = tenant_result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name=TENANT_NAME, funnel_config=FUNNEL_CONFIG)
            session.add(tenant)
            await session.flush()

        user_result = await session.execute(
            select(User).where(User.email == BENCHMARK_EMAIL)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                tenant_id=tenant.id,
                email=BENCHMARK_EMAIL,
                hashed_password=hash_password(BENCHMARK_PASSWORD),
            )
            session.add(user)
        else:
            user.tenant_id = tenant.id
            user.hashed_password = hash_password(BENCHMARK_PASSWORD)

        lead_ids_result = await session.execute(
            select(Lead.id).where(Lead.tenant_id == tenant.id)
        )
        existing_lead_ids = list(lead_ids_result.scalars().all())

        if existing_lead_ids:
            await session.execute(delete(Analysis).where(Analysis.lead_id.in_(existing_lead_ids)))
            await session.execute(delete(Message).where(Message.lead_id.in_(existing_lead_ids)))
            await session.execute(delete(Lead).where(Lead.id.in_(existing_lead_ids)))

        new_leads: list[Lead] = []
        for i in range(TOTAL_LEADS):
            lead = Lead(
                tenant_id=tenant.id,
                phone=f"55119{70000000 + i:08d}",
                name=f"Lead Benchmark {i + 1:02d}",
                status=LeadStatus.active,
                current_stage=FUNNEL_CONFIG["1"],
                temperature_score=None,
                analysis_status=AnalysisStatus.idle,
                analysis_error=None,
                analysis_requested_at=None,
                analysis_completed_at=None,
                is_processing=False,
                processing_started_at=None,
            )
            session.add(lead)
            new_leads.append(lead)

        await session.flush()

        all_messages: list[Message] = []
        for i, lead in enumerate(new_leads):
            started_at = now - timedelta(minutes=(TOTAL_LEADS - i))
            for msg_idx, (direction, content) in enumerate(_conversation_template(i)):
                all_messages.append(
                    Message(
                        lead_id=lead.id,
                        direction=direction,
                        content=content,
                        timestamp=started_at + timedelta(seconds=msg_idx * 40),
                    )
                )

        session.add_all(all_messages)
        await session.commit()

        print("Benchmark seed concluido")
        print(f"tenant_name={TENANT_NAME}")
        print(f"email={BENCHMARK_EMAIL}")
        print(f"password={BENCHMARK_PASSWORD}")
        print(f"leads_criados={TOTAL_LEADS}")
        print(f"mensagens_criadas={len(all_messages)}")


if __name__ == "__main__":
    asyncio.run(seed_benchmark())
