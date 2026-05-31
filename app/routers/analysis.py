import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Lead, LeadStatus, User
from app.schemas.analysis import AnalysisResponse, AnalyzeBatchResponse
from app.services.analysis_service import analyze_lead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["analysis"])

BATCH_SEMAPHORE = asyncio.Semaphore(5)  # Max 5 concurrent LLM calls


@router.post("/{lead_id}/analyze", response_model=AnalysisResponse)
async def analyze_single(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify lead belongs to user's tenant
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    if lead.status != LeadStatus.active:
        raise HTTPException(status_code=400, detail="Lead não está ativo")

    try:
        analysis = await analyze_lead(lead_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao analisar lead")

    return AnalysisResponse(
        id=str(analysis.id),
        lead_id=str(analysis.lead_id),
        temperature_score=analysis.temperature_score,
        current_stage=analysis.current_stage,
        conversation_summary=analysis.conversation_summary,
        qualitative_tips=analysis.qualitative_tips,
        suggested_reply=analysis.suggested_reply,
    )


@router.post("/analyze-all", response_model=AnalyzeBatchResponse)
async def analyze_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(
            Lead.tenant_id == current_user.tenant_id,
            Lead.status == LeadStatus.active,
            Lead.is_processing == False, # noqa
        )
    )
    leads = result.scalars().all()

    results = []

    async def _analyze_one(lead: Lead):
        async with BATCH_SEMAPHORE:
            try:
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    analysis = await analyze_lead(lead.id, session)
                    return {"lead_id": str(lead.id), "status": "ok", "temperature_score": analysis.temperature_score}
            except HTTPException as e:
                return {"lead_id": str(lead.id), "status": "error", "detail": e.detail}
            except Exception as e:
                logger.error(f"Error analyzing lead {lead.id}: {e}")
                return {"lead_id": str(lead.id), "status": "error", "detail": str(e)}

    tasks = [_analyze_one(lead) for lead in leads]
    results = await asyncio.gather(*tasks)

    succeeded = sum(1 for r in results if r["status"] == "ok")
    failed = sum(1 for r in results if r["status"] == "error")

    return AnalyzeBatchResponse(
        total=len(results),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )
