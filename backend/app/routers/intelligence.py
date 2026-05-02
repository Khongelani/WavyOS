"""
Intelligence router — web intelligence scan endpoints.

POST  /companies/{id}/intelligence/scan        trigger scan (background)
GET   /companies/{id}/intelligence/status      lightweight status poll
GET   /companies/{id}/intelligence             full report + contact discovery
POST  /companies/{id}/intelligence/scan/retry  retry a failed scan
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Company, ContactDiscovery, WebIntelligenceReport
from app.schemas import _parse_json_field
from app import web_intelligence_service

router = APIRouter(prefix="/companies", tags=["intelligence"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _latest_report(company_id: int, db: AsyncSession) -> WebIntelligenceReport | None:
    result = await db.execute(
        select(WebIntelligenceReport)
        .where(WebIntelligenceReport.company_id == company_id)
        .order_by(WebIntelligenceReport.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _latest_discovery(company_id: int, db: AsyncSession) -> ContactDiscovery | None:
    result = await db.execute(
        select(ContactDiscovery)
        .where(ContactDiscovery.company_id == company_id)
        .order_by(ContactDiscovery.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _serialize_report(r: WebIntelligenceReport) -> dict:
    return {
        "id": r.id,
        "scan_status": r.scan_status,
        "scan_triggered_by": r.scan_triggered_by,
        "scan_started_at": r.scan_started_at,
        "scan_completed_at": r.scan_completed_at,
        "scan_error": r.scan_error,
        "is_jse_listed": r.is_jse_listed,
        "jse_ticker": r.jse_ticker,
        "latest_stock_data": _parse_json_field(r.latest_stock_data, None),
        "news_articles": _parse_json_field(r.news_articles, []),
        "sens_announcements": _parse_json_field(r.sens_announcements, []),
        "leadership_mentions": _parse_json_field(r.leadership_mentions, []),
        "linkedin_company_url": r.linkedin_company_url,
        "leadership_page_url": r.leadership_page_url,
        "intelligence_summary": r.intelligence_summary,
        "key_signals": _parse_json_field(r.key_signals, []),
        "timing_assessment": r.timing_assessment,
        "recommended_approach": r.recommended_approach,
        "is_demo": r.is_demo,
        "created_at": r.created_at,
    }


def _serialize_discovery(d: ContactDiscovery) -> dict:
    return {
        "id": d.id,
        "recommended_roles": _parse_json_field(d.recommended_roles, []),
        "recommended_departments": _parse_json_field(d.recommended_departments, []),
        "linkedin_search_urls": _parse_json_field(d.linkedin_search_urls, []),
        "linkedin_company_page": d.linkedin_company_page,
        "contact_sources": _parse_json_field(d.contact_sources, []),
        "publicly_listed_contacts": _parse_json_field(d.publicly_listed_contacts, []),
        "is_demo": d.is_demo,
        "created_at": d.created_at,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{company_id}/intelligence/scan", status_code=202)
async def trigger_scan(
    company_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Trigger a web intelligence scan. Returns immediately; scan runs in background."""
    if not settings.ENABLE_WEB_INTELLIGENCE:
        raise HTTPException(status_code=503, detail="Web intelligence is disabled")

    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Cooldown check
    last = await _latest_report(company_id, db)
    if last and last.scan_started_at and last.scan_status in ("complete", "running"):
        elapsed = datetime.utcnow() - last.scan_started_at
        cooldown = timedelta(hours=settings.SCAN_COOLDOWN_HOURS)
        if elapsed < cooldown:
            mins = int(elapsed.total_seconds() / 60)
            raise HTTPException(
                status_code=429,
                detail=f"Scan cooldown active — last scan {mins} minutes ago",
            )

    # Create pending record
    report = WebIntelligenceReport(
        company_id=company_id,
        scan_status="pending",
        scan_triggered_by="manual",
        scan_started_at=datetime.utcnow(),
    )
    db.add(report)
    await db.commit()

    background_tasks.add_task(web_intelligence_service.run_full_scan, company_id)
    return {"message": "Scan started", "status": "pending"}


@router.post("/{company_id}/intelligence/scan/retry", status_code=202)
async def retry_scan(
    company_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Retry a failed scan without cooldown enforcement."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    background_tasks.add_task(web_intelligence_service.run_full_scan, company_id)
    return {"message": "Retry started", "status": "pending"}


@router.get("/{company_id}/intelligence/status")
async def get_intelligence_status(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Lightweight status poll — no heavy JSON fields."""
    report = await _latest_report(company_id, db)
    if not report:
        return {"status": "not_scanned", "completed_at": None, "started_at": None, "error": None}
    return {
        "status": report.scan_status,
        "completed_at": report.scan_completed_at,
        "started_at": report.scan_started_at,
        "error": report.scan_error,
    }


@router.get("/{company_id}/intelligence")
async def get_intelligence(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Full intelligence report + contact discovery for a company."""
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    report = await _latest_report(company_id, db)
    discovery = await _latest_discovery(company_id, db)

    return {
        "intelligence": _serialize_report(report) if report else None,
        "discovery": _serialize_discovery(discovery) if discovery else None,
    }
