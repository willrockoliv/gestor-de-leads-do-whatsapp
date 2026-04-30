import pytest
from httpx import AsyncClient
from app.models.models import Lead
from tests.fixtures_leads import seed_tenant_user_lead

@pytest.mark.anyio
async def test_lead_seed(client, seed_tenant_user_lead):
    # Garante que o lead de teste está presente e visível
    resp = await client.post("/auth/login", json={"email": "teste@teste.com", "password": "123456"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/leads", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(l["phone"] == "11999999999" and l["current_stage"] == "Prospecção" for l in data)
