import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from sqlalchemy import select

from app.main import app as fastapi_app
from app.models import Lead, LeadStatus, Message, SessionStatus, WhatsAppSession
from app.providers.whatsapp import ProviderSessionStatus, get_whatsapp_provider
from app.providers.whatsapp import waha as provider_module
from app.providers.whatsapp.interface import (WhatsAppProviderConflictError,
                                              WhatsAppProviderUnavailableError)
from app.routers import whatsapp as whatsapp_router
from app.services.whatsapp_session_service import sync_whatsapp_sessions
from tests.conftest import AsyncSessionTest


class MockWahaState:
    def __init__(self):
        self.sessions: dict[str, dict] = {}


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict | list):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _build_handler(state: MockWahaState):
    class MockWahaHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length == 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def do_GET(self):
            path = self.path

            if path == "/api/version":
                return _json_response(self, 200, {"version": "mock", "tier": "PLUS"})

            if path == "/api/server/environment":
                return _json_response(self, 200, {"WAHA_TIER": "PLUS"})

            if path.startswith("/api/sessions/"):
                session_id = path[len("/api/sessions/") :]
                if not session_id:
                    return _json_response(self, 404, {"message": "Not found"})
                item = state.sessions.get(session_id)
                if not item:
                    return _json_response(self, 404, {"message": "Session not found"})
                payload = {"name": session_id, "status": item["status"]}
                if item.get("phone"):
                    payload["me"] = {"id": f"{item['phone']}@c.us"}
                return _json_response(self, 200, payload)

            if path.startswith("/api/") and path.endswith("/auth/qr"):
                session_id = path[len("/api/") : -len("/auth/qr")].strip("/")
                item = state.sessions.get(session_id)
                if not item:
                    return _json_response(self, 404, {"message": "Session not found"})
                item["status"] = "SCAN_QR_CODE"
                item["qr"] = f"data:image/png;base64,mock-{session_id}"
                return _json_response(self, 200, {"qrCode": item["qr"]})

            if path.startswith("/sessions/") and path.endswith("/qrcode"):
                session_id = path[len("/sessions/") : -len("/qrcode")].strip("/")
                item = state.sessions.get(session_id)
                if not item:
                    return _json_response(self, 404, {"message": "Session not found"})
                item["status"] = "SCAN_QR_CODE"
                item["qr"] = f"data:image/png;base64,mock-{session_id}"
                return _json_response(self, 200, {"qrCode": item["qr"]})

            if path.startswith("/sessions/") and path.endswith("/status"):
                session_id = path[len("/sessions/") : -len("/status")].strip("/")
                item = state.sessions.get(session_id)
                if not item:
                    return _json_response(self, 404, {"message": "Session not found"})
                payload = {"status": item["status"]}
                if item.get("phone"):
                    payload["phoneNumber"] = item["phone"]
                return _json_response(self, 200, payload)

            return _json_response(self, 404, {"message": "Not found"})

        def do_POST(self):
            path = self.path

            if path in ("/api/sessions", "/sessions"):
                payload = self._read_json()
                session_id = payload.get("name") or payload.get("session")
                if not session_id:
                    return _json_response(self, 422, {"message": "Session name required"})
                if session_id in state.sessions:
                    return _json_response(
                        self,
                        422,
                        {"message": f"Session '{session_id}' already exists. Use PUT to update it."},
                    )
                state.sessions[session_id] = {"status": "PENDING", "phone": None, "qr": None}
                return _json_response(self, 201, {"name": session_id, "status": "PENDING"})

            if path.startswith("/api/sessions/") and path.endswith("/stop"):
                session_id = path[len("/api/sessions/") : -len("/stop")].strip("/")
                item = state.sessions.get(session_id)
                if not item:
                    return _json_response(self, 404, {"message": "Session not found"})
                item["status"] = "STOPPED"
                return _json_response(self, 200, {"name": session_id, "status": "STOPPED"})

            return _json_response(self, 404, {"message": "Not found"})

    return MockWahaHandler


@pytest.fixture
def mock_waha(monkeypatch):
    state = MockWahaState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _build_handler(state))
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://{host}:{port}"
    monkeypatch.setattr(provider_module.settings, "WHATSAPP_API_URL", base_url)
    monkeypatch.setattr(provider_module.settings, "WHATSAPP_API_KEY", "")
    monkeypatch.setattr(provider_module.settings, "WHATSAPP_WEBHOOK_URL", "http://test/webhooks/whatsapp")
    monkeypatch.setattr(provider_module.settings, "WHATSAPP_WEBHOOK_HMAC_KEY", "")
    whatsapp_router._limiter._store.clear()

    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
async def auth_user(client):
    resp = await client.post(
        "/auth/register",
        json={
            "email": f"e2e-whatsapp-{uuid.uuid4().hex[:8]}@test.com",
            "password": "12345678",
            "business_name": "E2E WhatsApp",
        },
    )
    token = resp.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"token": token, "tenant_id": me.json()["tenant_id"]}


async def test_e2e_connect_qrcode_status_flow(client, auth_user, mock_waha):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}

    connect = await client.post("/whatsapp/connect", headers=headers)
    assert connect.status_code == 200
    session_id = connect.json()["session_id"]
    assert connect.json()["status"] == "PENDING"

    qr = await client.get("/whatsapp/qrcode", headers=headers)
    assert qr.status_code == 200
    assert qr.json()["status"] == "QR_CODE_READY"
    assert qr.json()["qr_code"].startswith("data:image/png;base64,")

    mock_waha.sessions[session_id]["status"] = "STARTING"
    status_connecting = await client.get("/whatsapp/status", headers=headers)
    assert status_connecting.status_code == 200
    assert status_connecting.json()["status"] == "CONNECTING"

    mock_waha.sessions[session_id]["status"] = "WORKING"
    mock_waha.sessions[session_id]["phone"] = "5511999999999"
    status_connected = await client.get("/whatsapp/status", headers=headers)
    assert status_connected.status_code == 200
    assert status_connected.json()["status"] == "CONNECTED"
    assert status_connected.json()["phone"] == "5511999999999"


async def test_e2e_receive_message_from_webhook(client, auth_user, mock_waha):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}

    connect = await client.post("/whatsapp/connect", headers=headers)
    session_id = connect.json()["session_id"]
    mock_waha.sessions[session_id]["status"] = "WORKING"
    mock_waha.sessions[session_id]["phone"] = "5511888888888"

    payload = {
        "event": "message.upsert",
        "session": session_id,
        "data": {
            "key": {
                "remoteJid": "5511888888888@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG01",
            },
            "message": {"conversation": "Ola, quero mais informacoes"},
            "pushName": "Cliente E2E",
            "messageTimestamp": 1700000000,
        },
    }

    resp = await client.post("/webhooks/whatsapp", content=json.dumps(payload))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    async with AsyncSessionTest() as db:
        lead = (await db.execute(select(Lead).where(Lead.phone == "5511888888888"))).scalar_one()
        message = (await db.execute(select(Message).where(Message.lead_id == lead.id))).scalar_one()

        assert lead.is_processing is False
        assert message.content == "Ola, quero mais informacoes"


async def test_e2e_disconnect_sync_releases_processing_lock(client, auth_user, mock_waha):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}

    connect = await client.post("/whatsapp/connect", headers=headers)
    session_id = connect.json()["session_id"]

    tenant_id = uuid.UUID(auth_user["tenant_id"])
    async with AsyncSessionTest() as db:
        lead = Lead(
            tenant_id=tenant_id,
            phone="5511777777777",
            status=LeadStatus.active,
            is_processing=True,
            processing_started_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        )
        db.add(lead)
        await db.commit()

    mock_waha.sessions[session_id]["status"] = "STOPPED"

    async with AsyncSessionTest() as db:
        changed = await sync_whatsapp_sessions(db)
        assert changed >= 1

    async with AsyncSessionTest() as db:
        session = (await db.execute(select(WhatsAppSession).where(WhatsAppSession.tenant_id == tenant_id))).scalar_one()
        lead = (await db.execute(select(Lead).where(Lead.phone == "5511777777777"))).scalar_one()
        assert session.status == SessionStatus.DISCONNECTED
        assert lead.is_processing is False


async def test_e2e_rate_limiting_connect(client, auth_user, mock_waha):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}

    for _ in range(5):
        ok = await client.post("/whatsapp/connect", headers=headers)
        assert ok.status_code == 200

    blocked = await client.post("/whatsapp/connect", headers=headers)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers

    key = f"connect:{auth_user['tenant_id']}"
    whatsapp_router._limiter._store.pop(key, None)

    recovered = await client.post("/whatsapp/connect", headers=headers)
    assert recovered.status_code == 200


async def test_connect_with_provider_dependency_override(client, auth_user):
    class FakeProvider:
        async def resolve_session_id(self, tenant_id):
            return f"fake-{tenant_id}"

        async def create_session(self, db, tenant_id, session_id: str):
            return None

        async def fetch_qr_code(self, session_id: str):
            return "fake-qr"

        async def fetch_session_status(self, session_id: str):
            return ProviderSessionStatus(status=SessionStatus.CONNECTED, phone_number="5511990000000")

        async def stop_session(self, session_id: str):
            return None

        def normalize_webhook_payload(self, payload: dict):
            return None

    fastapi_app.dependency_overrides[get_whatsapp_provider] = lambda: FakeProvider()
    try:
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        resp = await client.post("/whatsapp/connect", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["session_id"].startswith("fake-")
    finally:
        fastapi_app.dependency_overrides.pop(get_whatsapp_provider, None)


async def test_connect_returns_502_when_provider_unavailable(client, auth_user):
    class DownProvider:
        async def resolve_session_id(self, tenant_id):
            return f"tenant-{tenant_id}"

        async def create_session(self, db, tenant_id, session_id: str):
            raise WhatsAppProviderUnavailableError("provider down")

        async def fetch_qr_code(self, session_id: str):
            return None

        async def fetch_session_status(self, session_id: str):
            return ProviderSessionStatus(status=SessionStatus.DISCONNECTED)

        async def stop_session(self, session_id: str):
            return None

        def normalize_webhook_payload(self, payload: dict):
            return None

    fastapi_app.dependency_overrides[get_whatsapp_provider] = lambda: DownProvider()
    try:
        headers = {"Authorization": f"Bearer {auth_user['token']}"}
        resp = await client.post("/whatsapp/connect", headers=headers)
        assert resp.status_code == 502
        assert resp.json()["detail"] == "Falha ao criar sessão no serviço WhatsApp"
    finally:
        fastapi_app.dependency_overrides.pop(get_whatsapp_provider, None)


async def test_connect_returns_409_on_core_default_conflict(client):
    class CoreConflictProvider:
        async def resolve_session_id(self, tenant_id):
            return "default"

        async def create_session(self, db, tenant_id, session_id: str):
            raise WhatsAppProviderConflictError(
                "WAHA CORE only supports a single shared session (default). "
                "Upgrade to WAHA PLUS for one session per tenant."
            )

        async def fetch_qr_code(self, session_id: str):
            return None

        async def fetch_session_status(self, session_id: str):
            return ProviderSessionStatus(status=SessionStatus.DISCONNECTED)

        async def stop_session(self, session_id: str):
            return None

        def normalize_webhook_payload(self, payload: dict):
            return None

    fastapi_app.dependency_overrides[get_whatsapp_provider] = lambda: CoreConflictProvider()
    try:
        register = await client.post(
            "/auth/register",
            json={
                "email": f"core-conflict-{uuid.uuid4().hex[:8]}@test.com",
                "password": "12345678",
                "business_name": "CORE Conflict",
            },
        )
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post("/whatsapp/connect", headers=headers)
        assert resp.status_code == 409
        assert "CORE only supports a single shared session" in resp.json()["detail"]
    finally:
        fastapi_app.dependency_overrides.pop(get_whatsapp_provider, None)
