import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text

from app.models import Lead, Message, Analysis, Tenant, LeadStatus
from app.schemas.analysis import LLMAnalysisResult

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_TEMPLATE = """Você é um assistente especializado em análise de leads de vendas via WhatsApp.
Analise a conversa abaixo e retorne APENAS um JSON válido com os seguintes campos:
- temperature_score: número inteiro de 0 a 100 indicando a "temperatura" do lead (0 = frio, 100 = quente)
- current_stage: a etapa atual do funil de vendas baseada nas etapas disponíveis
- conversation_summary: resumo conciso da conversa em português
- qualitative_tips: dicas qualitativas para o vendedor em português
- suggested_reply: sugestão de resposta para o vendedor enviar em português

Etapas do funil disponíveis:
{funnel_stages}

Retorne APENAS o JSON, sem markdown, sem explicações."""


def build_analysis_prompt(funnel_config: dict, messages: list[Message]) -> tuple[str, str]:
    """Build system and user prompts for LLM analysis. Returns (system_prompt, user_prompt)."""
    stages = "\n".join(f"- {v}" for v in funnel_config.values())
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(funnel_stages=stages)

    conversation_lines = []
    for msg in messages:
        prefix = "VENDEDOR" if msg.direction.value == "outbound" else "LEAD"
        conversation_lines.append(f"[{prefix}]: {msg.content}")

    user_prompt = "Conversa:\n" + "\n".join(conversation_lines)
    return system_prompt, user_prompt


def parse_llm_response(response_text: str) -> LLMAnalysisResult:
    """Parse and validate LLM response JSON."""
    # Strip potential markdown code blocks
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return LLMAnalysisResult.model_validate(data)


async def acquire_lock(lead_id: uuid.UUID, db: AsyncSession) -> bool:
    """
    Attempt to acquire processing lock via optimistic locking.
    Returns True if lock acquired, False if already locked.
    Uses atomic UPDATE ... WHERE to prevent race conditions.
    """
    result = await db.execute(
        update(Lead)
        .where(Lead.id == lead_id, Lead.is_processing == False)
        .values(is_processing=True, processing_started_at=datetime.now(timezone.utc))
        .returning(Lead.id)
    )
    await db.commit()
    return result.scalar_one_or_none() is not None


async def release_lock(lead_id: uuid.UUID, db: AsyncSession) -> None:
    """Release processing lock."""
    await db.execute(
        update(Lead)
        .where(Lead.id == lead_id)
        .values(is_processing=False, processing_started_at=None)
    )
    await db.commit()


async def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM via litellm. Isolated for easy mocking in tests."""
    from litellm import acompletion
    from app.core.config import get_settings

    settings = get_settings()
    response = await acompletion(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_key=settings.LLM_API_KEY,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def analyze_lead(lead_id: uuid.UUID, db: AsyncSession) -> Analysis:
    """
    Full analysis pipeline for a single lead:
    1. Acquire lock (or raise 409)
    2. Load lead + messages + tenant funnel
    3. Call LLM
    4. Parse response
    5. Persist Analysis and update Lead
    6. Release lock
    """
    if not await acquire_lock(lead_id, db):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead já está sendo processado",
        )

    try:
        # Load lead with tenant
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one()

        result = await db.execute(select(Tenant).where(Tenant.id == lead.tenant_id))
        tenant = result.scalar_one()

        # Load messages
        result = await db.execute(
            select(Message).where(Message.lead_id == lead_id).order_by(Message.timestamp)
        )
        messages = result.scalars().all()

        if not messages:
            await release_lock(lead_id, db)
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Lead não possui mensagens")

        system_prompt, user_prompt = build_analysis_prompt(tenant.funnel_config, messages)
        response_text = await call_llm(system_prompt, user_prompt)
        parsed = parse_llm_response(response_text)

        analysis = Analysis(
            lead_id=lead_id,
            temperature_score=parsed.temperature_score,
            current_stage=parsed.current_stage,
            conversation_summary=parsed.conversation_summary,
            qualitative_tips=parsed.qualitative_tips,
            suggested_reply=parsed.suggested_reply,
        )
        db.add(analysis)

        lead.temperature_score = parsed.temperature_score
        lead.current_stage = parsed.current_stage

        await db.commit()
        await db.refresh(analysis)
        return analysis
    finally:
        await release_lock(lead_id, db)


async def reset_zombie_locks(db: AsyncSession, timeout_minutes: int = 5) -> int:
    """Reset locks stuck for more than timeout_minutes. Returns count of reset leads."""
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
    result = await db.execute(
        update(Lead)
        .where(Lead.is_processing == True, Lead.processing_started_at < cutoff)
        .values(is_processing=False, processing_started_at=None)
        .returning(Lead.id)
    )
    await db.commit()
    reset_ids = result.scalars().all()

    if reset_ids:
        logger.warning(f"Watchdog: reset {len(reset_ids)} zombie locks: {reset_ids}")

    return len(reset_ids)


def build_analysis_prompt_sync(funnel_config: dict, messages_data: list[dict]) -> tuple[str, str]:
    """Pure sync version for unit testing."""
    stages = "\n".join(f"- {v}" for v in funnel_config.values())
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(funnel_stages=stages)

    conversation_lines = []
    for msg in messages_data:
        prefix = "VENDEDOR" if msg["direction"] == "outbound" else "LEAD"
        conversation_lines.append(f"[{prefix}]: {msg['content']}")

    user_prompt = "Conversa:\n" + "\n".join(conversation_lines)
    return system_prompt, user_prompt
