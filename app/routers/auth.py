from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import get_current_user
from app.models import User
from app.schemas.auth import (TokenResponse, UserLogin, UserRegister,
                              UserResponse)
from app.services.auth_service import authenticate_user, register_user
from app.services.funnel_templates import list_funnel_templates

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
_login_limiter = SlidingWindowRateLimiter()


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
async def login(payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    key = f"login:{client_ip}:{payload.email.lower()}"
    allowed, retry_after = _login_limiter.hit(
        key,
        limit=settings.AUTH_LOGIN_RATE_LIMIT,
        window_seconds=settings.AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
            headers={"Retry-After": str(retry_after)},
        )

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
