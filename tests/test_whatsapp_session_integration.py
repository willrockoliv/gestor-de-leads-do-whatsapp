import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models import SessionStatus, WhatsAppSession


@pytest.fixture
async def auth_user(client):
    resp = await client.post(
        "/auth/register",
        json={
            "email": f"whatsapp-{uuid.uuid4().hex[:8]}@test.com",
            "password": "senha123",
            "business_name": "Loja WhatsApp",
        },
    )
    token = resp.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"token": token, "tenant_id": me.json()["tenant_id"]}


async def test_connect_creates_session(client, auth_user, monkeypatch):
    from app.routers import whatsapp
    from tests.conftest import AsyncSessionTest

    async def fake_create_session(self, tenant_id):
        async with AsyncSessionTest() as session:
            existing = await whatsapp._get_session_for_tenant(session, tenant_id)
            if existing:
                return existing
            wa = WhatsAppSession(
                tenant_id=tenant_id,
                session_id=f"tenant-{tenant_id}",
                status=SessionStatus.PENDING,
            )
            session.add(wa)
            await session.commit()
            await session.refresh(wa)
            return wa

    monkeypatch.setattr("app.services.whatsapp_session_service.WhatsAppSessionService.create_session", fake_create_session)

    resp = await client.post("/whatsapp/connect", headers={"Authorization": f"Bearer {auth_user['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["session_id"].startswith("tenant-")


async def test_qrcode_returns_payload(client, auth_user, monkeypatch):
    from app.services.whatsapp_session_service import WhatsAppSessionService
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.UUID(auth_user["tenant_id"])
    async with AsyncSessionTest() as session:
        wa = WhatsAppSession(
            tenant_id=tenant_id,
            session_id=f"tenant-{tenant_id}",
            status=SessionStatus.PENDING,
            qr_code_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        session.add(wa)
        await session.commit()

    async def fake_get_qr(self, session):
        session.qr_code = "data:image/png;base64,abc"
        session.qr_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        session.status = SessionStatus.QR_CODE_READY
        await self.db.commit()
        await self.db.refresh(session)
        return session

    monkeypatch.setattr(WhatsAppSessionService, "get_qr_code", fake_get_qr)

    resp = await client.get("/whatsapp/qrcode", headers={"Authorization": f"Bearer {auth_user['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "QR_CODE_READY"
    assert data["qr_code"].startswith("data:image/png;base64,")


async def test_status_returns_connected(client, auth_user, monkeypatch):
    from app.services.whatsapp_session_service import WhatsAppSessionService
    from tests.conftest import AsyncSessionTest

    tenant_id = uuid.UUID(auth_user["tenant_id"])
    async with AsyncSessionTest() as session:
        wa = WhatsAppSession(
            tenant_id=tenant_id,
            session_id=f"tenant-{tenant_id}",
            status=SessionStatus.CONNECTING,
        )
        session.add(wa)
        await session.commit()

    async def fake_check_status(self, session):
        session.status = SessionStatus.CONNECTED
        session.phone_number = "5511999999999"
        session.connected_since = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    monkeypatch.setattr(WhatsAppSessionService, "check_connection_status", fake_check_status)

    resp = await client.get("/whatsapp/status", headers={"Authorization": f"Bearer {auth_user['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CONNECTED"
    assert data["phone"] == "5511999999999"


async def test_connect_rate_limit(client, auth_user, monkeypatch):
    from app.routers import whatsapp
    from app.services.whatsapp_session_service import WhatsAppSessionService

    whatsapp._limiter._store.clear()

    async def fake_create_session(self, tenant_id):
        return WhatsAppSession(
            tenant_id=tenant_id,
            session_id=f"tenant-{tenant_id}",
            status=SessionStatus.PENDING,
        )

    monkeypatch.setattr(WhatsAppSessionService, "create_session", fake_create_session)

    for _ in range(5):
        ok = await client.post("/whatsapp/connect", headers={"Authorization": f"Bearer {auth_user['token']}"})
        assert ok.status_code == 200

    blocked = await client.post("/whatsapp/connect", headers={"Authorization": f"Bearer {auth_user['token']}"})
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


async def test_connect_core_conflict_returns_409(client, auth_user, monkeypatch):
    from app.services.whatsapp_session_service import WhatsAppSessionService

    async def fake_create_session(self, tenant_id):
        raise RuntimeError(
            "WAHA CORE only supports a single shared session (default). "
            "Upgrade to WAHA PLUS for one session per tenant."
        )

    monkeypatch.setattr(WhatsAppSessionService, "create_session", fake_create_session)

    resp = await client.post("/whatsapp/connect", headers={"Authorization": f"Bearer {auth_user['token']}"})
    assert resp.status_code == 409
    assert "WAHA CORE only supports a single shared session" in resp.json()["detail"]
