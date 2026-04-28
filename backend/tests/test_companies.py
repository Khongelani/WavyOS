import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PipelineStage
from tests.conftest import TestSessionLocal


async def create_stage(db: AsyncSession, name: str = "Target Identified", order: int = 1):
    stage = PipelineStage(name=name, order_index=order, color="#64748B")
    db.add(stage)
    await db.commit()
    await db.refresh(stage)
    return stage


@pytest.mark.asyncio
async def test_create_company(auth_client):
    async with TestSessionLocal() as db:
        stage = await create_stage(db)

    resp = await auth_client.post("/companies", json={
        "name": "Test Corp",
        "industry": "Finance",
        "country": "South Africa",
        "pipeline_stage_id": stage.id,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Corp"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_companies(auth_client):
    await auth_client.post("/companies", json={"name": "Alpha Ltd"})
    await auth_client.post("/companies", json={"name": "Beta Inc"})

    resp = await auth_client.get("/companies")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_research_returns_valid_structure(auth_client):
    comp = await auth_client.post("/companies", json={"name": "Demo Company", "industry": "Mining"})
    company_id = comp.json()["id"]

    resp = await auth_client.post(f"/companies/{company_id}/research", json={})
    assert resp.status_code == 201
    data = resp.json()
    assert "overview" in data
    assert "signals" in data
    assert isinstance(data["signals"], list)
    assert "confidence_score" in data
    assert data["is_demo"] == True  # No API key in test env


@pytest.mark.asyncio
async def test_brief_generation(auth_client):
    comp = await auth_client.post("/companies", json={"name": "Brief Test Co", "industry": "Logistics"})
    company_id = comp.json()["id"]

    research_resp = await auth_client.post(f"/companies/{company_id}/research", json={})
    research_id = research_resp.json()["id"]

    brief_resp = await auth_client.post(f"/companies/{company_id}/briefs", json={"research_id": research_id})
    assert brief_resp.status_code == 201
    data = brief_resp.json()
    assert "executive_signal" in data
    assert "conversation_opener" in data
    assert data["is_demo"] == True


@pytest.mark.asyncio
async def test_pipeline_stage_update(auth_client):
    async with TestSessionLocal() as db:
        stage1 = await create_stage(db, "Target Identified", 1)
        stage2 = await create_stage(db, "Researched", 2)

    comp = await auth_client.post("/companies", json={
        "name": "Stage Test Corp",
        "pipeline_stage_id": stage1.id,
    })
    company_id = comp.json()["id"]

    update_resp = await auth_client.put(f"/companies/{company_id}", json={"pipeline_stage_id": stage2.id})
    assert update_resp.status_code == 200
    assert update_resp.json()["pipeline_stage_id"] == stage2.id
