from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date

from app.database import get_db
from app.models import Company, Contact, OutreachDraft, SignalBrief, ResearchReport, Task, PipelineStage
from app.schemas import DashboardStats, TaskOut
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    total_companies = await db.scalar(select(func.count()).select_from(Company))
    companies_researched = await db.scalar(
        select(func.count(Company.id.distinct())).select_from(Company).join(ResearchReport, isouter=False)
    )
    contacts_added = await db.scalar(select(func.count()).select_from(Contact))
    outreach_drafts = await db.scalar(select(func.count()).select_from(OutreachDraft))
    briefs_generated = await db.scalar(select(func.count()).select_from(SignalBrief))

    # "Call Booked" is stage 6
    calls_booked = await db.scalar(
        select(func.count()).select_from(Company).where(Company.pipeline_stage_id == 6)
    )

    # Today's tasks (due today or overdue, still pending)
    today = datetime.utcnow().replace(hour=23, minute=59, second=59)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    q = select(Task).where(
        Task.status == "pending",
        Task.due_date <= today,
    ).order_by(Task.due_date.asc()).limit(10)
    result = await db.execute(q)
    today_tasks = result.scalars().all()

    return DashboardStats(
        total_companies=total_companies or 0,
        companies_researched=companies_researched or 0,
        contacts_added=contacts_added or 0,
        outreach_drafts=outreach_drafts or 0,
        calls_booked=calls_booked or 0,
        briefs_generated=briefs_generated or 0,
        today_tasks=[TaskOut.model_validate(t) for t in today_tasks],
    )
