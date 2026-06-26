from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Create async engine with execution options to set default schema
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    execution_options={"schema_translate_map": {None: "leads"}}
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    metadata = MetaData(schema="leads")


async def get_db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session
