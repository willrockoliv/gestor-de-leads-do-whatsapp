import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Analysis, Lead, LeadStatus, Message, User
from app.schemas.lead import (AnalysisSummary, DashboardStats, LeadDetail,
                              LeadListItem, LeadStageUpdate, LeadStatusUpdate,
                              MessageItem, PaginatedMessages)

router = APIRouter(tags=["dashboard"])


@router.get("/leads", response_model=list[LeadListItem])
async def list_leads(
    status: str | None = Query(None, description="Filter by status"),
    stage: str | None = Query(None, description="Filter by stage"),
    min_score: int | None = Query(None, ge=0, le=100),
    max_score: int | None = Query(None, ge=0, le=100),
    sort_by: str = Query("temperature_score", description="Sort field"),
    order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.tenant_id == current_user.tenant_id)

    if status:
        query = query.where(Lead.status == status)
    else:
        query = query.where(Lead.status == LeadStatus.active)

    if stage:
        query = query.where(Lead.current_stage == stage)
    if min_score is not None:
        query = query.where(Lead.temperature_score >= min_score)
    if max_score is not None:
        query = query.where(Lead.temperature_score <= max_score)

    # Sort
    sort_col = getattr(Lead, sort_by, Lead.temperature_score)
    if order == "asc":
        query = query.order_by(sort_col.asc().nullslast())
    else:
        query = query.order_by(sort_col.desc().nullslast())

    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    leads = result.scalars().all()

    items = []
    for lead in leads:
        # Calculate conversation time
        conv_time = None
        msg_result = await db.execute(
            select(
                func.min(Message.timestamp).label("first_msg"),
                func.max(Message.timestamp).label("last_msg"),
            ).where(Message.lead_id == lead.id)
        )
        row = msg_result.one_or_none()
        if row and row.first_msg and row.last_msg:
            delta = row.last_msg - row.first_msg
            conv_time = delta.total_seconds() / 60.0

        items.append(LeadListItem(
            id=str(lead.id),
            phone=lead.phone,
            name=lead.name,
            status=lead.status.value,
            current_stage=lead.current_stage,
            temperature_score=lead.temperature_score,
            is_processing=lead.is_processing,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
            conversation_time_minutes=conv_time,
        ))

    return items


@router.get("/leads/{lead_id}", response_model=LeadDetail)
async def get_lead(
    lead_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    # Conversation time
    conv_time = None
    msg_result = await db.execute(
        select(
            func.min(Message.timestamp).label("first_msg"),
            func.max(Message.timestamp).label("last_msg"),
        ).where(Message.lead_id == lead.id)
    )
    row = msg_result.one_or_none()
    if row and row.first_msg and row.last_msg:
        delta = row.last_msg - row.first_msg
        conv_time = delta.total_seconds() / 60.0

    # Latest analysis
    analysis_result = await db.execute(
        select(Analysis).where(Analysis.lead_id == lead.id).order_by(Analysis.created_at.desc()).limit(1)
    )
    analysis = analysis_result.scalar_one_or_none()

    latest_analysis = None
    if analysis:
        latest_analysis = AnalysisSummary(
            id=str(analysis.id),
            temperature_score=analysis.temperature_score,
            current_stage=analysis.current_stage,
            conversation_summary=analysis.conversation_summary,
            qualitative_tips=analysis.qualitative_tips,
            suggested_reply=analysis.suggested_reply,
            created_at=analysis.created_at,
        )

    return LeadDetail(
        id=str(lead.id),
        phone=lead.phone,
        name=lead.name,
        status=lead.status.value,
        current_stage=lead.current_stage,
        temperature_score=lead.temperature_score,
        is_processing=lead.is_processing,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        conversation_time_minutes=conv_time,
        latest_analysis=latest_analysis,
    )


@router.get("/leads/{lead_id}/messages", response_model=PaginatedMessages)
async def get_messages(
    lead_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify lead ownership
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.lead_id == lead_id)
    )
    total = count_result.scalar()

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.lead_id == lead_id)
        .order_by(Message.timestamp.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()

    return PaginatedMessages(
        items=[
            MessageItem(
                id=str(m.id),
                direction=m.direction.value,
                content=m.content,
                timestamp=m.timestamp,
            )
            for m in messages
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: uuid.UUID,
    payload: LeadStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.status not in ("converted", "lost"):
        raise HTTPException(status_code=400, detail="Status deve ser 'converted' ou 'lost'")

    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    lead.status = LeadStatus(payload.status)
    await db.commit()
    return {"status": "ok", "lead_id": str(lead_id), "new_status": payload.status}


@router.patch("/leads/{lead_id}/stage")
async def update_lead_stage(
    lead_id: uuid.UUID,
    payload: LeadStageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    lead.current_stage = payload.current_stage
    await db.commit()
    return {"status": "ok", "lead_id": str(lead_id), "new_stage": payload.current_stage}


@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id

    # Count by status
    count_result = await db.execute(
        select(
            func.count().filter(Lead.status == LeadStatus.active).label("active"),
            func.count().filter(Lead.status == LeadStatus.converted).label("converted"),
            func.count().filter(Lead.status == LeadStatus.lost).label("lost"),
            func.avg(
                case(
                    (Lead.status == LeadStatus.active, Lead.temperature_score),
                    else_=None,
                )
            ).label("avg_temp"),
        ).where(Lead.tenant_id == tenant_id)
    )
    row = count_result.one()

    # Count by stage (active only)
    stage_result = await db.execute(
        select(Lead.current_stage, func.count().label("cnt"))
        .where(Lead.tenant_id == tenant_id, Lead.status == LeadStatus.active)
        .group_by(Lead.current_stage)
    )
    leads_by_stage = {
        (stage or "Sem etapa"): cnt
        for stage, cnt in stage_result.all()
    }

    return DashboardStats(
        total_active=row.active,
        total_converted=row.converted,
        total_lost=row.lost,
        leads_by_stage=leads_by_stage,
        avg_temperature=round(row.avg_temp, 1) if row.avg_temp else None,
    )

