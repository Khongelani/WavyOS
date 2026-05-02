import pytest
from app.config import settings


@pytest.mark.asyncio
async def test_valid_login(client):
    resp = await client.post("/auth/login", json={
        "email": settings.OWNER_EMAIL,
        "password": settings.OWNER_PASSWORD,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_password(client):
    resp = await client.post("/auth/login", json={
        "email": settings.OWNER_EMAIL,
        "password": "wrong_password",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": settings.OWNER_PASSWORD,
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    resp = await client.get("/companies")
    assert resp.status_code == 401
