from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional
import json
from datetime import datetime

from app.database import get_db
from app.models import Company, ResearchReport, SignalBrief, Contact, Task, WeeklySnapshot
from app.schemas import CompanyCreate, CompanyUpdate, CompanyOut, CompanyListOut, ResearchRequest, ResearchOut, BriefGenerateRequest, BriefOut, BriefUpdate
from app.auth import get_current_user
from app import ai_service
from app.routers.execution import get_or_create_snapshot, current_week_start

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=List[CompanyListOut])
async def list_companies(
    search: Optional[str] = None,
    stage_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    q = select(Company)
    if search:
        q = q.where(Company.name.ilike(f"%{search}%"))
    if stage_id:
        q = q.where(Company.pipeline_stage_id == stage_id)
    q = q.order_by(Company.created_at.desc())
    result = await db.execute(q)
    companies = result.scalars().all()

    out = []
    for c in companies:
        research_count = await db.scalar(select(func.count()).where(ResearchReport.company_id == c.id))
        brief_count = await db.scalar(select(func.count()).where(SignalBrief.company_id == c.id))
        contact_count = await db.scalar(select(func.count()).where(Contact.company_id == c.id))
        item = CompanyListOut.model_validate(c)
        item.research_count = research_count or 0
        item.brief_count = brief_count or 0
        item.contact_count = contact_count or 0
        out.append(item)
    return out


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = Company(**data.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return CompanyOut.model_validate(company)


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(company)


@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    company.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(company)
    return CompanyOut.model_validate(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await db.delete(company)
    await db.commit()


# ── Research ──────────────────────────────────────────────────────────────────

@router.get("/{company_id}/research", response_model=List[ResearchOut])
async def list_research(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    q = select(ResearchReport).where(ResearchReport.company_id == company_id).order_by(ResearchReport.created_at.desc())
    result = await db.execute(q)
    reports = result.scalars().all()
    return [ResearchOut.from_orm(r) for r in reports]


@router.post("/{company_id}/research", response_model=ResearchOut, status_code=status.HTTP_201_CREATED)
async def run_research(
    company_id: int,
    req: ResearchRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    name = req.company_name or company.name
    website = req.website or company.website
    industry = req.industry or company.industry

    data = await ai_service.research_company(name, website, industry)

    report = ResearchReport(
        company_id=company_id,
        overview=data.get("overview"),
        signals=json.dumps(data.get("recent_signals", [])),
        cashflow_pressures=json.dumps(data.get("cashflow_pressure_points", [])),
        buyer_personas=json.dumps(data.get("buyer_personas", [])),
        outreach_angle=data.get("outreach_angle"),
        confidence_score=data.get("confidence_score", 0.0),
        source_links=json.dumps(data.get("source_links", [])),
        is_demo=data.get("is_demo", False),
    )
    db.add(report)

    # Auto-advance pipeline stage to "Researched" (stage 2) if still at stage 1
    if company.pipeline_stage_id in (None, 1):
        company.pipeline_stage_id = 2
        company.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(report)

    # Increment companies_researched in snapshot (only for real AI research, not demo)
    if not report.is_demo:
        week_start = current_week_start()
        await get_or_create_snapshot(db)
        await db.execute(
            update(WeeklySnapshot)
            .where(WeeklySnapshot.week_start_date == week_start)
            .values(
                companies_researched=WeeklySnapshot.companies_researched + 1,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()

    return ResearchOut.from_orm(report)


# ── Signal Briefs ─────────────────────────────────────────────────────────────

@router.get("/{company_id}/briefs", response_model=List[BriefOut])
async def list_briefs(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    q = select(SignalBrief).where(SignalBrief.company_id == company_id).order_by(SignalBrief.created_at.desc())
    result = await db.execute(q)
    briefs = result.scalars().all()
    return [BriefOut.from_orm(b) for b in briefs]


@router.post("/{company_id}/briefs", response_model=BriefOut, status_code=status.HTTP_201_CREATED)
async def generate_brief(
    company_id: int,
    req: BriefGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    research = await db.get(ResearchReport, req.research_id)
    if not research or research.company_id != company_id:
        raise HTTPException(status_code=404, detail="Research report not found")

    from app.schemas import _parse_json_field
    research_data = {
        "overview": research.overview,
        "recent_signals": _parse_json_field(research.signals, []),
        "cashflow_pressure_points": _parse_json_field(research.cashflow_pressures, []),
        "outreach_angle": research.outreach_angle,
    }

    data = await ai_service.generate_signal_brief(company.name, research_data)

    brief = SignalBrief(
        company_id=company_id,
        research_id=req.research_id,
        executive_signal=data.get("executive_signal"),
        why_it_matters=data.get("why_it_matters"),
        receivables_blind_spots=json.dumps(data.get("receivables_blind_spots", [])),
        operational_impact=data.get("operational_impact"),
        suggested_action=data.get("suggested_action"),
        conversation_opener=data.get("conversation_opener"),
        is_demo=data.get("is_demo", False),
    )
    db.add(brief)
    await db.commit()
    await db.refresh(brief)
    return BriefOut.from_orm(brief)


@router.put("/{company_id}/briefs/{brief_id}", response_model=BriefOut)
async def update_brief(
    company_id: int,
    brief_id: int,
    data: BriefUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    brief = await db.get(SignalBrief, brief_id)
    if not brief or brief.company_id != company_id:
        raise HTTPException(status_code=404, detail="Brief not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "receivables_blind_spots" and isinstance(value, list):
            setattr(brief, field, json.dumps(value))
        else:
            setattr(brief, field, value)
    brief.is_edited = True
    await db.commit()
    await db.refresh(brief)
    return BriefOut.from_orm(brief)
