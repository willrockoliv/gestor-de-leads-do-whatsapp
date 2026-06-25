import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from litellm import acompletion
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.prompts import ANALYSIS_SYSTEM_PROMPT, REINFORCED_USER_PROMPT_SUFFIX
from app.models import Analysis, AnalysisStatus, Lead, LeadStatus, Message, Tenant
from app.schemas.analysis import AnalyzeStatusCounts, AnalyzeStatusResponse, LLMAnalysisResult

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 500


def build_analysis_prompt(funnel_config: dict, messages: list[Message]) -> tuple[str, str]:
    """Build system and user prompts for LLM analysis."""
    settings = get_settings()
    template = ANALYSIS_SYSTEM_PROMPT

    stages = "\n".join(f"- {v}" for v in funnel_config.values())
    system_prompt = template.format(funnel_stages=stages)

    conversation_lines = []
    for msg in messages[-settings.ANALYSIS_MAX_CONTEXT_MESSAGES :]:
        prefix = "VENDEDOR" if msg.direction.value == "outbound" else "LEAD"
        conversation_lines.append(f"[{prefix}]: {msg.content}")

    user_prompt = "Conversa:\n" + "\n".join(conversation_lines)
    return system_prompt, user_prompt


def parse_llm_response(response_text: str) -> LLMAnalysisResult:
    """Parse and validate LLM response JSON."""
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return LLMAnalysisResult.model_validate(data)


async def parse_llm_response_with_retry(
    response_text: str,
    system_prompt: str,
    user_prompt: str,
    retries: int,
) -> LLMAnalysisResult:
    """Retry LLM call when JSON parsing/validation fails."""
    try:
        return parse_llm_response(response_text)
    except Exception as exc:
        if retries <= 0:
            raise

        logger.warning(
            "Parse failure, retrying with reinforced format prompt (remaining=%s): %s",
            retries,
            exc,
        )
        reinforced_user_prompt = user_prompt + REINFORCED_USER_PROMPT_SUFFIX
        retried_response = await call_llm(system_prompt, reinforced_user_prompt)
        return await parse_llm_response_with_retry(
            retried_response,
            system_prompt,
            user_prompt,
            retries=retries - 1,
        )


def _normalize_error(exc: Exception | str) -> str:
    message = str(exc).strip() if not isinstance(exc, str) else exc.strip()
    if not message:
        return "Erro desconhecido durante análise"
    return message[:MAX_ERROR_LENGTH]


async def queue_lead_analysis(lead_id: uuid.UUID, db: AsyncSession) -> str:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(Lead)
        .where(
            Lead.id == lead_id,
            Lead.analysis_status.notin_([AnalysisStatus.pending, AnalysisStatus.processing]),
        )
        .values(
            analysis_status=AnalysisStatus.pending,
            analysis_error=None,
            analysis_requested_at=now,
            analysis_completed_at=None,
            is_processing=False,
            processing_started_at=None,
        )
        .returning(Lead.id)
    )
    await db.commit()

    queued_id = result.scalar_one_or_none()
    if queued_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead já está na fila de análise",
        )

    return str(queued_id)


async def queue_all_leads_for_analysis(tenant_id: uuid.UUID, db: AsyncSession) -> list[str]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(Lead)
        .where(
            Lead.tenant_id == tenant_id,
            Lead.status == LeadStatus.active,
            Lead.analysis_status.notin_([AnalysisStatus.pending, AnalysisStatus.processing]),
        )
        .values(
            analysis_status=AnalysisStatus.pending,
            analysis_error=None,
            analysis_requested_at=now,
            analysis_completed_at=None,
            is_processing=False,
            processing_started_at=None,
        )
        .returning(Lead.id)
    )
    await db.commit()
    return [str(lead_id) for lead_id in result.scalars().all()]


async def get_analysis_status(
    tenant_id: uuid.UUID,
    db: AsyncSession,
    lead_ids: list[uuid.UUID] | None = None,
) -> AnalyzeStatusResponse:
    """Return status aggregates for a tenant, optionally filtered to specific lead_ids."""
    base_where = [Lead.tenant_id == tenant_id]
    if lead_ids:
        base_where.append(Lead.id.in_(lead_ids))

    counts_result = await db.execute(
        select(Lead.analysis_status, func.count())
        .where(*base_where)
        .group_by(Lead.analysis_status)
    )
    counts_map = {status.value: total for status, total in counts_result.all()}

    ids_result = await db.execute(
        select(Lead.id, Lead.analysis_status)
        .where(
            *base_where,
            Lead.analysis_status.in_(
                [
                    AnalysisStatus.pending,
                    AnalysisStatus.processing,
                    AnalysisStatus.completed,
                    AnalysisStatus.failed,
                ]
            ),
        )
    )
    grouped_ids: dict[str, list[str]] = {
        AnalysisStatus.pending.value: [],
        AnalysisStatus.processing.value: [],
        AnalysisStatus.completed.value: [],
        AnalysisStatus.failed.value: [],
    }
    for lead_id, analysis_status in ids_result.all():
        grouped_ids[analysis_status.value].append(str(lead_id))

    return AnalyzeStatusResponse(
        counts=AnalyzeStatusCounts(
            idle=counts_map.get(AnalysisStatus.idle.value, 0),
            pending=counts_map.get(AnalysisStatus.pending.value, 0),
            processing=counts_map.get(AnalysisStatus.processing.value, 0),
            completed=counts_map.get(AnalysisStatus.completed.value, 0),
            failed=counts_map.get(AnalysisStatus.failed.value, 0),
        ),
        pending_ids=grouped_ids[AnalysisStatus.pending.value],
        processing_ids=grouped_ids[AnalysisStatus.processing.value],
        completed_ids=grouped_ids[AnalysisStatus.completed.value],
        failed_ids=grouped_ids[AnalysisStatus.failed.value],
    )


async def get_lead_analysis_status(
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[str, str | None]:
    """Return (analysis_status, analysis_error) for a lead in tenant scope."""
    result = await db.execute(
        select(Lead.analysis_status, Lead.analysis_error).where(
            Lead.id == lead_id,
            Lead.tenant_id == tenant_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado")
    analysis_status, analysis_error = row
    return analysis_status.value, analysis_error


async def _mark_analysis_failed(lead_id: uuid.UUID, db: AsyncSession, error: Exception | str) -> None:
    await db.execute(
        update(Lead)
        .where(Lead.id == lead_id)
        .values(
            analysis_status=AnalysisStatus.failed,
            analysis_error=_normalize_error(error),
            analysis_completed_at=datetime.now(timezone.utc),
            is_processing=False,
            processing_started_at=None,
        )
    )
    await db.commit()


async def claim_next_pending_lead(db: AsyncSession) -> uuid.UUID | None:
    """Claim the next pending lead using fair round-robin per tenant.

    Selects the oldest pending lead per tenant (rank 1), then picks the globally
    oldest among those candidates. The UPDATE WHERE analysis_status=pending acts
    as an optimistic lock: if another worker claimed the same lead between the
    SELECT and the UPDATE, RETURNING returns nothing and we return None — the
    outer worker loop will retry on the next cycle.
    """
    ranked_pending = (
        select(
            Lead.id.label("lead_id"),
            func.row_number()
            .over(
                partition_by=Lead.tenant_id,
                order_by=(Lead.analysis_requested_at.asc().nullslast(), Lead.created_at.asc()),
            )
            .label("tenant_rank"),
            Lead.analysis_requested_at.label("requested_at"),
            Lead.created_at.label("created_at"),
        )
        .where(Lead.analysis_status == AnalysisStatus.pending)
        .subquery()
    )

    next_result = await db.execute(
        select(ranked_pending.c.lead_id)
        .where(ranked_pending.c.tenant_rank == 1)
        .order_by(ranked_pending.c.requested_at.asc().nullslast(), ranked_pending.c.created_at.asc())
        .limit(1)
    )
    lead_id = next_result.scalar_one_or_none()
    if lead_id is None:
        return None

    claimed = await db.execute(
        update(Lead)
        .where(Lead.id == lead_id, Lead.analysis_status == AnalysisStatus.pending)
        .values(
            analysis_status=AnalysisStatus.processing,
            analysis_error=None,
            is_processing=True,
            processing_started_at=datetime.now(timezone.utc),
        )
        .returning(Lead.id)
    )
    await db.commit()
    return claimed.scalar_one_or_none()


async def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM via litellm. Isolated for easy mocking in tests."""
    settings = get_settings()
    response = await acompletion(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        api_key=settings.LLM_API_KEY,
        api_base=settings.LLM_API_BASE or None,
        max_tokens=settings.ANALYSIS_MAX_OUTPUT_TOKENS,
        timeout=30,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def process_lead_analysis(lead_id: uuid.UUID, db: AsyncSession) -> Analysis:
    """Run analysis for a lead already claimed by the worker."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one()

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == lead.tenant_id))
    tenant = tenant_result.scalar_one()

    messages_result = await db.execute(
        select(Message).where(Message.lead_id == lead_id).order_by(Message.timestamp)
    )
    messages = messages_result.scalars().all()
    if not messages:
        raise ValueError("Lead não possui mensagens para análise")

    system_prompt, user_prompt = build_analysis_prompt(tenant.funnel_config, messages)
    settings = get_settings()
    response_text = await call_llm(system_prompt, user_prompt)
    parsed = await parse_llm_response_with_retry(
        response_text,
        system_prompt,
        user_prompt,
        retries=max(settings.ANALYSIS_JSON_PARSE_RETRIES - 1, 0),
    )

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
    lead.analysis_status = AnalysisStatus.completed
    lead.analysis_error = None
    lead.analysis_completed_at = datetime.now(timezone.utc)
    lead.is_processing = False
    lead.processing_started_at = None

    await db.commit()
    await db.refresh(analysis)
    return analysis


async def process_next_pending_lead(db: AsyncSession) -> bool:
    lead_id = await claim_next_pending_lead(db)
    if lead_id is None:
        return False

    try:
        await process_lead_analysis(lead_id, db)
    except Exception as exc:
        logger.error("Error processing queued analysis for lead %s: %s", lead_id, exc)
        await _mark_analysis_failed(lead_id, db, exc)

    return True


async def reset_zombie_locks(db: AsyncSession, timeout_minutes: int = 5) -> int:
    """Reset locks stuck for more than timeout_minutes. Returns count of reset leads."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
    result = await db.execute(
        update(Lead)
        .where(Lead.analysis_status == AnalysisStatus.processing, Lead.processing_started_at < cutoff)
        .values(
            analysis_status=AnalysisStatus.pending,
            analysis_error="Processamento reiniciado pelo watchdog",
            is_processing=False,
            processing_started_at=None,
        )
        .returning(Lead.id)
    )
    await db.commit()
    reset_ids = result.scalars().all()

    if reset_ids:
        logger.warning("Watchdog: reset %s zombie locks: %s", len(reset_ids), reset_ids)

    return len(reset_ids)
