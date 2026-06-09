

async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_health_includes_security_headers(client):
    resp = await client.get("/health")
    assert resp.status_code == 200

    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy") == "no-referrer"
    assert resp.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"
    assert "default-src 'none'" in resp.headers.get("content-security-policy", "")
    assert "max-age=" in resp.headers.get("strict-transport-security", "")
