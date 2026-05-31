

async def test_register(client):
    resp = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "senha123",
        "business_name": "Loja Teste",
        "funnel_template": "default",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client):
    await client.post("/auth/register", json={
        "email": "dup@example.com",
        "password": "senha123",
        "business_name": "Loja 1",
    })
    resp = await client.post("/auth/register", json={
        "email": "dup@example.com",
        "password": "senha456",
        "business_name": "Loja 2",
    })
    assert resp.status_code == 409


async def test_login(client):
    await client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "senha123",
        "business_name": "Loja Login",
    })
    resp = await client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "senha123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "wrong@example.com",
        "password": "senha123",
        "business_name": "Loja Wrong",
    })
    resp = await client.post("/auth/login", json={
        "email": "wrong@example.com",
        "password": "senhaerrada",
    })
    assert resp.status_code == 401


async def test_login_nonexistent_user(client):
    resp = await client.post("/auth/login", json={
        "email": "naoexiste@example.com",
        "password": "senha123",
    })
    assert resp.status_code == 401


async def test_me_authenticated(client):
    reg = await client.post("/auth/register", json={
        "email": "me@example.com",
        "password": "senha123",
        "business_name": "Loja Me",
    })
    token = reg.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert "tenant_id" in data


async def test_me_unauthenticated(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token(client):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


async def test_get_funnel_templates(client):
    resp = await client.get("/auth/funnel-templates")
    assert resp.status_code == 200
    data = resp.json()
    assert "default" in data
    assert "servicos" in data
    assert "ecommerce" in data
    assert "imobiliaria" in data


async def test_update_funnel(client):
    reg = await client.post("/auth/register", json={
        "email": "funnel@example.com",
        "password": "senha123",
        "business_name": "Loja Funnel",
    })
    token = reg.json()["access_token"]

    new_funnel = {"etapa_1": "Contato", "etapa_2": "Proposta", "etapa_3": "Fechou"}
    resp = await client.put(
        "/tenants/me/funnel",
        json={"funnel_config": new_funnel},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["funnel_config"] == new_funnel


async def test_get_tenant(client):
    reg = await client.post("/auth/register", json={
        "email": "tenant@example.com",
        "password": "senha123",
        "business_name": "Loja Tenant",
        "funnel_template": "ecommerce",
    })
    token = reg.json()["access_token"]

    resp = await client.get("/tenants/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Loja Tenant"
    assert "Interesse" in data["funnel_config"].values()


async def test_register_with_custom_template(client):
    reg = await client.post("/auth/register", json={
        "email": "template@example.com",
        "password": "senha123",
        "business_name": "Imobiliária Top",
        "funnel_template": "imobiliaria",
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    resp = await client.get("/tenants/me", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert "Visita Agendada" in data["funnel_config"].values()
