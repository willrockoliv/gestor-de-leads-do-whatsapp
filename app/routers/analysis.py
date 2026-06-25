import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import get_current_user
from app.models import AnalysisStatus, Lead, LeadStatus, User
from app.schemas.analysis import (AnalyzeBatchResponse,
                                  AnalysisLeadStatusResponse,
                                  AnalyzeStatusResponse,
                                  AnalysisJobAcceptedResponse)
from app.services.analysis_service import (get_analysis_status,
                                           get_lead_analysis_status,
                                           queue_all_leads_for_analysis,
                                           queue_lead_analysis)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["analysis"])
settings = get_settings()
_analysis_limiter = SlidingWindowRateLimiter()


@router.post(
    "/{lead_id}/analyze",
    response_model=AnalysisJobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enfileirar análise de um lead",
    description=(
        "Solicita a análise assíncrona de um lead ativo do tenant autenticado. "
        "A resposta retorna `202 Accepted` e o lead passa para o status `pending`, "
        "devendo ser acompanhado pelos endpoints de status."
    ),
    responses={
        202: {"description": "Lead aceito para processamento assíncrono."},
        400: {"description": "Lead não está ativo para análise."},
        404: {"description": "Lead não encontrado no tenant autenticado."},
        409: {"description": "Lead já está pendente ou em processamento."},
        429: {"description": "Rate limit excedido para solicitação de análise."},
    },
)
async def analyze_single(
    lead_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = f"analyze-single:{current_user.tenant_id}:{request.url.path}"
    allowed, retry_after = _analysis_limiter.hit(
        key,
        limit=settings.ANALYSIS_RATE_LIMIT,
        window_seconds=settings.ANALYSIS_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    # Verify lead belongs to user's tenant
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    if lead.status != LeadStatus.active:
        raise HTTPException(status_code=400, detail="Lead não está ativo")
    if lead.analysis_status in (AnalysisStatus.pending, AnalysisStatus.processing):
        raise HTTPException(status_code=409, detail="Lead já está na fila de análise")

    try:
        await queue_lead_analysis(lead_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enfileirar análise do lead")

    return AnalysisJobAcceptedResponse(
        lead_id=str(lead_id),
        analysis_status=AnalysisStatus.pending.value,
    )


@router.get(
    "/analyze/status",
    response_model=AnalyzeStatusResponse,
    summary="Consultar status agregado das análises",
    description=(
        "Retorna contadores e listas de IDs por status de análise (`pending`, `processing`, "
        "`completed`, `failed`) no tenant autenticado. Pode ser filtrado com `lead_ids` para "
        "acompanhar apenas um subconjunto enfileirado."
    ),
    responses={
        200: {"description": "Status agregado retornado com sucesso."},
        401: {"description": "Usuário não autenticado."},
    },
)
async def analyze_status(
    lead_ids: list[uuid.UUID] | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Consulta o panorama agregado da fila de análise do tenant."""
    return await get_analysis_status(
        current_user.tenant_id,
        db,
        lead_ids=lead_ids,
    )


@router.post(
    "/analyze-all",
    response_model=AnalyzeBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enfileirar análise em lote",
    description=(
        "Solicita a análise assíncrona de todos os leads ativos do tenant autenticado. "
        "A resposta retorna `202 Accepted`, a quantidade enfileirada e os IDs aceitos."
    ),
    responses={
        202: {"description": "Lote aceito para processamento assíncrono."},
        429: {"description": "Rate limit excedido para enfileiramento em lote."},
    },
)
async def analyze_all(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enfileira todos os leads ativos do tenant para análise assíncrona."""
    key = f"analyze-all:{current_user.tenant_id}:{request.url.path}"
    allowed, retry_after = _analysis_limiter.hit(
        key,
        limit=settings.ANALYSIS_RATE_LIMIT,
        window_seconds=settings.ANALYSIS_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    queued_ids = await queue_all_leads_for_analysis(current_user.tenant_id, db)

    return AnalyzeBatchResponse(
        total_enqueued=len(queued_ids),
        lead_ids=queued_ids,
    )


@router.get(
    "/{lead_id}/analyze/status",
    response_model=AnalysisLeadStatusResponse,
    summary="Consultar status de análise de um lead",
    description=(
        "Retorna o status atual da análise de um lead específico, incluindo a mensagem de erro "
        "padronizada quando o processamento termina em `failed`."
    ),
    responses={
        200: {"description": "Status individual retornado com sucesso."},
        404: {"description": "Lead não encontrado no tenant autenticado."},
    },
)
async def analyze_single_status(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Consulta o status da análise de um lead específico."""
    analysis_status, analysis_error = await get_lead_analysis_status(
        current_user.tenant_id,
        lead_id,
        db,
    )
    return AnalysisLeadStatusResponse(
        lead_id=str(lead_id),
        analysis_status=analysis_status,
        analysis_error=analysis_error,
    )
