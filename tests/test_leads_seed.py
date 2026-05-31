import pytest

from tests.fixtures_leads import seed_tenant_user_lead  # noqa


@pytest.mark.anyio
async def test_lead_seed(client, seed_tenant_user_lead): # noqa
    # Garante que o lead de teste está presente e visível
    resp = await client.post("/auth/login", json={"email": "teste@teste.com", "password": "123456"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/leads", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(lead["phone"] == "11999999999" and lead["current_stage"] == "Prospecção" for lead in data)
