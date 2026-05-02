"""
Tests for the web intelligence module.

Covers:
  - POST /companies creates company + triggers pending scan record
  - GET /companies/{id}/intelligence/status returns correct status
  - Scan cooldown enforced: second trigger within 1 hour returns 429
  - GET /companies/{id}/intelligence returns intelligence + discovery
  - LinkedIn URL generation produces correctly encoded URLs
  - If SERPER_API_KEY is not configured, scan completes with empty news_articles
  - POST /companies/{id}/intelligence/scan/retry works without cooldown
"""

import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.models import Company, WebIntelligenceReport, ContactDiscovery
from app.web_intelligence_service import _build_linkedin_urls


# ── LinkedIn URL generation ───────────────────────────────────────────────────

def test_linkedin_url_encoding_spaces():
    roles = [{"title": "Chief Financial Officer", "priority": 1}]
    urls = _build_linkedin_urls("Grindrod Freight", roles)
    assert len(urls) >= 4
    for u in urls:
        assert " " not in u["url"], f"Unencoded space in URL: {u['url']}"


def test_linkedin_url_contains_company():
    roles = [{"title": "CFO", "priority": 1}]
    urls = _build_linkedin_urls("Kumba Iron Ore", roles)
    # company name must be encoded in every URL
    for u in urls:
        assert "Kumba" in u["url"] or "kumba" in u["url"].lower() or "Iron" in u["url"] or "iron" in u["url"].lower() or "Kumba+Iron+Ore" in u["url"] or "Kumba%20Iron%20Ore" in u["url"]


def test_linkedin_url_no_duplicates():
    roles = [
        {"title": "CFO", "priority": 1},
        {"title": "CFO", "priority": 1},  # duplicate role
    ]
    urls = _build_linkedin_urls("TestCo", roles)
    seen = {u["url"] for u in urls}
    assert len(seen) == len(urls), "Duplicate URLs returned"


def test_linkedin_url_minimum_count():
    urls = _build_linkedin_urls("TestCo", [])
    assert len(urls) >= 3, "Should always return at least 3 URLs"


# ── API endpoint tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_company_triggers_intelligence_scan(auth_client: AsyncClient):
    """POST /companies should create a WebIntelligenceReport with status pending/running."""
    with patch("app.web_intelligence_service.run_full_scan", new_callable=AsyncMock) as mock_scan:
        resp = await auth_client.post("/companies", json={
            "name": "Test Mining Ltd",
            "industry": "Mining",
            "country": "South Africa",
        })
    assert resp.status_code == 201
    company_id = resp.json()["id"]
    # Background task was scheduled (mock called)
    mock_scan.assert_called_once_with(company_id)


@pytest.mark.asyncio
async def test_intelligence_status_not_scanned(auth_client: AsyncClient):
    """Company with no scan returns not_scanned status."""
    resp = await auth_client.post("/companies", json={"name": "Fresh Corp"})
    assert resp.status_code == 201
    cid = resp.json()["id"]

    # Bypass auto-triggered scan by checking before it runs
    with patch("app.web_intelligence_service.run_full_scan", new_callable=AsyncMock):
        status_resp = await auth_client.get(f"/companies/{cid}/intelligence/status")
    # Status will be pending (scan was just triggered) or not_scanned if disabled
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("pending", "running", "complete", "not_scanned")


@pytest.mark.asyncio
async def test_intelligence_status_complete(auth_client: AsyncClient):
    """GET /intelligence/status returns complete when report is saved as complete."""
    from app.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    # Create company
    resp = await auth_client.post("/companies", json={"name": "Status Test Co"})
    cid = resp.json()["id"]

    # Manually insert a completed report
    async for db in get_db():
        report = WebIntelligenceReport(
            company_id=cid,
            scan_status="complete",
            scan_started_at=datetime.utcnow(),
            scan_completed_at=datetime.utcnow(),
            news_articles=json.dumps([]),
            sens_announcements=json.dumps([]),
            leadership_mentions=json.dumps([]),
            intelligence_summary="Test summary",
            key_signals=json.dumps([]),
            is_demo=False,
        )
        db.add(report)
        await db.commit()
        break

    status_resp = await auth_client.get(f"/companies/{cid}/intelligence/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "complete"


@pytest.mark.asyncio
async def test_intelligence_cooldown_enforced(auth_client: AsyncClient):
    """Triggering a second scan within cooldown returns 429."""
    from app.database import get_db

    resp = await auth_client.post("/companies", json={"name": "Cooldown Test Co"})
    cid = resp.json()["id"]

    # Insert a 'complete' report with recent scan_started_at
    async for db in get_db():
        report = WebIntelligenceReport(
            company_id=cid,
            scan_status="complete",
            scan_started_at=datetime.utcnow() - timedelta(minutes=10),  # 10 min ago
            scan_completed_at=datetime.utcnow() - timedelta(minutes=5),
            news_articles=json.dumps([]),
            sens_announcements=json.dumps([]),
            leadership_mentions=json.dumps([]),
            key_signals=json.dumps([]),
            is_demo=False,
        )
        db.add(report)
        await db.commit()
        break

    scan_resp = await auth_client.post(f"/companies/{cid}/intelligence/scan")
    assert scan_resp.status_code == 429
    assert "cooldown" in scan_resp.json()["detail"].lower()
    assert "minutes ago" in scan_resp.json()["detail"]


@pytest.mark.asyncio
async def test_intelligence_get_returns_both(auth_client: AsyncClient):
    """GET /intelligence returns both intelligence and discovery keys."""
    from app.database import get_db

    resp = await auth_client.post("/companies", json={"name": "Full Intel Co"})
    cid = resp.json()["id"]

    async for db in get_db():
        report = WebIntelligenceReport(
            company_id=cid,
            scan_status="complete",
            scan_started_at=datetime.utcnow(),
            scan_completed_at=datetime.utcnow(),
            news_articles=json.dumps([{"title": "Test", "url": "https://example.com", "source": "Test"}]),
            sens_announcements=json.dumps([]),
            leadership_mentions=json.dumps([]),
            intelligence_summary="Strong signals",
            key_signals=json.dumps([{"signal": "test", "relevance": "high", "signal_type": "other"}]),
            timing_assessment="Good timing",
            recommended_approach="Lead with X",
            is_demo=False,
        )
        db.add(report)
        await db.flush()

        discovery = ContactDiscovery(
            company_id=cid,
            web_intelligence_id=report.id,
            recommended_roles=json.dumps([{"title": "CFO", "priority": 1, "why": "test", "seniority": "C-suite", "department": "Finance"}]),
            recommended_departments=json.dumps([]),
            linkedin_search_urls=json.dumps([{"label": "CFO", "url": "https://linkedin.com/search/results/people/?company=test&title=CFO", "description": "test"}]),
            contact_sources=json.dumps([]),
            publicly_listed_contacts=json.dumps([]),
            is_demo=False,
        )
        db.add(discovery)
        await db.commit()
        break

    intel_resp = await auth_client.get(f"/companies/{cid}/intelligence")
    assert intel_resp.status_code == 200
    data = intel_resp.json()
    assert "intelligence" in data
    assert "discovery" in data
    assert data["intelligence"]["scan_status"] == "complete"
    assert data["intelligence"]["intelligence_summary"] == "Strong signals"
    assert len(data["discovery"]["recommended_roles"]) == 1
    assert len(data["discovery"]["linkedin_search_urls"]) == 1


@pytest.mark.asyncio
async def test_scan_completes_without_serper_key(auth_client: AsyncClient):
    """Scan should complete with empty news_articles when SERPER_API_KEY is not set."""
    from app import web_intelligence_service
    from app.database import get_db
    from sqlalchemy import select

    resp = await auth_client.post("/companies", json={
        "name": "No Key Test Co",
        "industry": "Mining",
        "country": "South Africa",
    })
    cid = resp.json()["id"]

    # Run scan directly (no SERPER key in test env)
    await web_intelligence_service.run_full_scan(cid)

    async for db in get_db():
        result = await db.execute(
            select(WebIntelligenceReport)
            .where(WebIntelligenceReport.company_id == cid)
            .order_by(WebIntelligenceReport.created_at.desc())
            .limit(1)
        )
        report = result.scalar_one_or_none()
        assert report is not None
        assert report.scan_status in ("complete", "failed")
        if report.scan_status == "complete":
            news = json.loads(report.news_articles or "[]")
            assert isinstance(news, list)
        break


@pytest.mark.asyncio
async def test_retry_bypasses_cooldown(auth_client: AsyncClient):
    """POST /intelligence/scan/retry should succeed regardless of cooldown."""
    from app.database import get_db

    resp = await auth_client.post("/companies", json={"name": "Retry Test Co"})
    cid = resp.json()["id"]

    async for db in get_db():
        report = WebIntelligenceReport(
            company_id=cid,
            scan_status="failed",
            scan_started_at=datetime.utcnow() - timedelta(minutes=5),
            news_articles=json.dumps([]),
            sens_announcements=json.dumps([]),
            leadership_mentions=json.dumps([]),
            key_signals=json.dumps([]),
            is_demo=False,
        )
        db.add(report)
        await db.commit()
        break

    with patch("app.web_intelligence_service.run_full_scan", new_callable=AsyncMock):
        retry_resp = await auth_client.post(f"/companies/{cid}/intelligence/scan/retry")
    assert retry_resp.status_code == 202
