import pytest
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import WeeklySnapshot, Company, Contact, ResearchReport, OutreachDraft, Task, PipelineStage
from tests.conftest import TestSessionLocal


def this_week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


@pytest.mark.asyncio
async def test_snapshot_created_on_first_call(auth_client):
    resp = await auth_client.get("/execution/snapshot/current")
    assert resp.status_code == 200
    data = resp.json()
    assert data["messages_sent"] == 0
    assert data["week_start_date"] == this_week_start().isoformat()


@pytest.mark.asyncio
async def test_snapshot_idempotent(auth_client):
    resp1 = await auth_client.get("/execution/snapshot/current")
    resp2 = await auth_client.get("/execution/snapshot/current")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["id"] == resp2.json()["id"]


@pytest.mark.asyncio
async def test_increment_messages_sent(auth_client):
    # Ensure snapshot exists
    await auth_client.get("/execution/snapshot/current")

    resp = await auth_client.patch("/execution/snapshot/increment", json={"field": "messages_sent"})
    assert resp.status_code == 200

    snap = await auth_client.get("/execution/snapshot/current")
    assert snap.json()["messages_sent"] == 1


@pytest.mark.asyncio
async def test_increment_invalid_field(auth_client):
    resp = await auth_client.patch("/execution/snapshot/increment", json={"field": "invalid_field"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_mark_draft_sent_creates_task_and_increments(auth_client):
    async with TestSessionLocal() as db:
        stage = PipelineStage(name="Target Identified", order_index=1, color="#64748B")
        db.add(stage)
        await db.flush()

        company = Company(name="Test Corp", pipeline_stage_id=stage.id)
        db.add(company)
        await db.flush()

        contact = Contact(name="Test Contact", company_id=company.id)
        db.add(contact)
        await db.flush()

        draft = OutreachDraft(
            contact_id=contact.id,
            company_id=company.id,
            linkedin_message="Test message",
            status="draft",
        )
        db.add(draft)
        await db.commit()
        draft_id = draft.id
        contact_id = contact.id
        company_id = company.id

    # Ensure snapshot row exists first
    await auth_client.get("/execution/snapshot/current")

    resp = await auth_client.put(f"/execution/outreach/{draft_id}/mark-sent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "sent"
    assert data["marked_sent_at"] is not None
    assert data["followup_due_at"] is not None

    # Check follow-up task was created
    async with TestSessionLocal() as db:
        tasks_result = await db.execute(
            select(Task).where(Task.contact_id == contact_id, Task.task_type == "followup")
        )
        tasks = tasks_result.scalars().all()
        assert len(tasks) == 1
        assert tasks[0].status == "pending"

    # Check snapshot was incremented
    snap = await auth_client.get("/execution/snapshot/current")
    assert snap.json()["messages_sent"] == 1


@pytest.mark.asyncio
async def test_alert_al01_triggered(auth_client):
    async with TestSessionLocal() as db:
        # Snapshot with 0 messages sent (already default 0)
        stage = PipelineStage(name="Stage 1", order_index=1, color="#64748B")
        db.add(stage)
        await db.flush()

        # Create 3 non-demo research reports this week
        company = Company(name="Alert Corp", pipeline_stage_id=stage.id)
        db.add(company)
        await db.flush()

        for _ in range(3):
            r = ResearchReport(
                company_id=company.id,
                overview="Test",
                is_demo=False,
                created_at=datetime.utcnow(),
            )
            db.add(r)
        await db.commit()

    # Snapshot with 0 messages
    await auth_client.get("/execution/snapshot/current")

    resp = await auth_client.get("/execution/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    al01_ids = [a["id"] for a in alerts]
    assert "AL01" in al01_ids


@pytest.mark.asyncio
async def test_alert_al01_not_triggered_when_messages_sent(auth_client):
    async with TestSessionLocal() as db:
        stage = PipelineStage(name="Stage 1b", order_index=1, color="#64748B")
        db.add(stage)
        await db.flush()

        company = Company(name="No Alert Corp", pipeline_stage_id=stage.id)
        db.add(company)
        await db.flush()

        for _ in range(3):
            r = ResearchReport(
                company_id=company.id,
                overview="Test",
                is_demo=False,
                created_at=datetime.utcnow(),
            )
            db.add(r)
        await db.commit()

    # Ensure snapshot exists and increment messages_sent
    await auth_client.get("/execution/snapshot/current")
    await auth_client.patch("/execution/snapshot/increment", json={"field": "messages_sent"})

    resp = await auth_client.get("/execution/alerts")
    assert resp.status_code == 200
    al01_ids = [a["id"] for a in resp.json()]
    assert "AL01" not in al01_ids
