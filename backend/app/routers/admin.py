import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db, engine
from app.models import Company, Contact, Task, ResearchReport, SignalBrief
from app.schemas import HealthStatus
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    ai_status = "configured" if settings.OPENAI_API_KEY else "demo_mode"

    return HealthStatus(api="ok", database=db_status, ai=ai_status)


@router.get("/export/{entity}")
async def export_csv(
    entity: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    allowed = {"companies", "contacts", "tasks"}
    if entity not in allowed:
        raise HTTPException(status_code=400, detail=f"Entity must be one of: {', '.join(allowed)}")

    output = io.StringIO()
    writer = csv.writer(output)

    if entity == "companies":
        result = await db.execute(select(Company).order_by(Company.created_at))
        rows = result.scalars().all()
        writer.writerow(["id", "name", "industry", "website", "country", "status", "pipeline_stage_id", "created_at"])
        for r in rows:
            writer.writerow([r.id, r.name, r.industry, r.website, r.country, r.status, r.pipeline_stage_id, r.created_at])

    elif entity == "contacts":
        result = await db.execute(select(Contact).order_by(Contact.created_at))
        rows = result.scalars().all()
        writer.writerow(["id", "company_id", "name", "role", "email", "linkedin_url", "contact_type", "outreach_status", "created_at"])
        for r in rows:
            writer.writerow([r.id, r.company_id, r.name, r.role, r.email, r.linkedin_url, r.contact_type, r.outreach_status, r.created_at])

    elif entity == "tasks":
        result = await db.execute(select(Task).order_by(Task.created_at))
        rows = result.scalars().all()
        writer.writerow(["id", "company_id", "contact_id", "description", "due_date", "status", "task_type", "created_at"])
        for r in rows:
            writer.writerow([r.id, r.company_id, r.contact_id, r.description, r.due_date, r.status, r.task_type, r.created_at])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}.csv"},
    )


@router.delete("/demo-data", status_code=200)
async def clear_demo_data(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    from sqlalchemy import delete

    # Delete in correct order to avoid FK constraints
    await db.execute(delete(Task).where(Task.is_demo == True))
    await db.execute(delete(ResearchReport).where(ResearchReport.is_demo == True))

    # Get demo brief IDs first, then delete outreach drafts linked to them
    from app.models import OutreachDraft
    demo_brief_result = await db.execute(select(SignalBrief.id).where(SignalBrief.is_demo == True))
    demo_brief_ids = [row[0] for row in demo_brief_result.all()]
    if demo_brief_ids:
        await db.execute(delete(OutreachDraft).where(OutreachDraft.brief_id.in_(demo_brief_ids)))

    await db.execute(delete(SignalBrief).where(SignalBrief.is_demo == True))
    await db.execute(delete(OutreachDraft).where(OutreachDraft.is_demo == True))

    await db.commit()
    return {"message": "Demo data cleared"}
