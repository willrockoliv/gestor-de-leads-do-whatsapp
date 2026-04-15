from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.schemas.tenant import FunnelUpdate, TenantResponse
from app.services.auth_service import register_user, authenticate_user
from app.services.funnel_templates import list_funnel_templates
from app.models import User, Tenant

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    _, token = await register_user(
        email=payload.email,
        password=payload.password,
        business_name=payload.business_name,
        funnel_template=payload.funnel_template,
        db=db,
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    _, token = await authenticate_user(
        email=payload.email,
        password=payload.password,
        db=db,
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        tenant_id=str(current_user.tenant_id),
    )


@router.get("/funnel-templates")
async def get_funnel_templates():
    return list_funnel_templates()
