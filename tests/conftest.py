
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"
# Default test environment variables for webhooks and providers
os.environ.setdefault("WEBHOOK_URL", "http://localhost:8000/webhooks/whatsapp")
# Leave WEBHOOK_HMAC_SECRET empty by default so unsigned webhooks are accepted in tests
os.environ.setdefault("WEBHOOK_HMAC_SECRET", "")
os.environ.setdefault("WHATSAPP_PROVIDER", "waha")
os.environ.setdefault("SECURITY_CSP", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.database import Base, get_db
from app.main import app as fastapi_app

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionTest = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

_LEADS_ATTACH = "ATTACH DATABASE 'file:leads_test_schema?mode=memory&cache=shared&uri=true' AS leads"

# SQLite doesn't support schemas natively; attach a shared in-memory database
# named 'leads' so schema-qualified table names (leads.xxx) resolve correctly.
@event.listens_for(engine_test.sync_engine, "connect")
def _attach_leads_schema(dbapi_conn, _):
    dbapi_conn.execute(_LEADS_ATTACH)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with AsyncSessionTest() as session:
        yield session


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
