from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models import User, Tenant
from app.core.security import hash_password, verify_password, create_access_token
from app.services.funnel_templates import get_funnel_template


async def register_user(
    email: str,
    password: str,
    business_name: str,
    funnel_template: str,
    db: AsyncSession,
) -> tuple[User, str]:
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )

    funnel_config = get_funnel_template(funnel_template)
    tenant = Tenant(name=business_name, funnel_config=funnel_config)
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


async def authenticate_user(
    email: str,
    password: str,
    db: AsyncSession,
) -> tuple[User, str]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


def register_user_sync(email: str, password: str, business_name: str, funnel_template: str) -> dict:
    """Pure sync version for unit testing (no DB)."""
    funnel_config = get_funnel_template(funnel_template)
    hashed = hash_password(password)
    return {
        "email": email,
        "hashed_password": hashed,
        "business_name": business_name,
        "funnel_config": funnel_config,
    }
