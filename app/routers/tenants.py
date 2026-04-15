from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.tenant import FunnelUpdate, TenantResponse
from app.models import User, Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.put("/me/funnel", response_model=TenantResponse)
async def update_funnel(
    payload: FunnelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one()
    tenant.funnel_config = payload.funnel_config
    await db.commit()
    await db.refresh(tenant)
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        funnel_config=tenant.funnel_config,
    )


@router.get("/me", response_model=TenantResponse)
async def get_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one()
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        funnel_config=tenant.funnel_config,
    )
