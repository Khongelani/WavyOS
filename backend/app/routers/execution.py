import json
from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    WeeklySnapshot, WeeklyReview, OutreachDraft, OutreachDraftStatus,
    Contact, OutreachStatus, Task, TaskStatus, ResearchReport, SignalBrief,
    Company
)
from app.auth import get_current_user
from app import ai_service

router = APIRouter(prefix="/execution", tags=["execution"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def current_week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())  # Monday


async def get_or_create_snapshot(db: AsyncSession) -> WeeklySnapshot:
    week_start = current_week_start()
    snap = await db.scalar(
        select(WeeklySnapshot).where(WeeklySnapshot.week_start_date == week_start)
    )
    if not snap:
        snap = WeeklySnapshot(
            week_start_date=week_start,
            messages_sent=0, followups_sent=0, briefs_sent=0,
            calls_requested=0, replies_received=0, companies_researched=0,
        )
        db.add(snap)
        await db.commit()
        await db.refresh(snap)
    return snap


# ── Schemas ───────────────────────────────────────────────────────────────────

class SnapshotOut(BaseModel):
    id: int
    week_start_date: date
    messages_sent: int
    followups_sent: int
    briefs_sent: int
    calls_requested: int
    replies_received: int
    companies_researched: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class IncrementRequest(BaseModel):
    field: str


INCREMENTABLE_FIELDS = {
    "messages_sent", "followups_sent", "briefs_sent",
    "calls_requested", "replies_received", "companies_researched"
}


class AlertOut(BaseModel):
    id: str
    text: str
    priority: int


class ReviewOut(BaseModel):
    id: int
    week_start_date: date
    what_was_sent: Optional[str] = None
    who_replied: Optional[str] = None
    what_worked: Optional[str] = None
    industry_response: Optional[str] = None
    change_next_week: Optional[str] = None
    generated_targets: Optional[List[str]] = None
    generated_angle: Optional[str] = None
    top_followups: Optional[List[dict]] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj: WeeklyReview):
        return cls(
            id=obj.id,
            week_start_date=obj.week_start_date,
            what_was_sent=obj.what_was_sent,
            who_replied=obj.who_replied,
            what_worked=obj.what_worked,
            industry_response=obj.industry_response,
            change_next_week=obj.change_next_week,
            generated_angle=obj.generated_angle,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            generated_targets=_parse_json(obj.generated_targets, []),
            top_followups=_parse_json(obj.top_followups, []),
        )

    model_config = {"from_attributes": True}


class ReviewUpdate(BaseModel):
    what_was_sent: Optional[str] = None
    who_replied: Optional[str] = None
    what_worked: Optional[str] = None
    industry_response: Optional[str] = None
    change_next_week: Optional[str] = None


class ReviewGenerateRequest(BaseModel):
    what_worked: Optional[str] = None
    industry_response: Optional[str] = None


class MarkSentOut(BaseModel):
    id: int
    status: str
    marked_sent_at: Optional[datetime] = None
    followup_due_at: Optional[datetime] = None
    contact_status_after: Optional[str] = None
    model_config = {"from_attributes": True}


def _parse_json(val, default):
    if val is None:
        return default
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return default


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/snapshot/current", response_model=SnapshotOut)
async def get_current_snapshot(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    snap = await get_or_create_snapshot(db)
    return snap


@router.patch("/snapshot/increment", status_code=200)
async def increment_snapshot(
    req: IncrementRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    if req.field not in INCREMENTABLE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid field: {req.field}")

    week_start = current_week_start()

    # Ensure row exists
    await get_or_create_snapshot(db)

    # Atomic increment — avoid read-modify-write
    col = getattr(WeeklySnapshot, req.field)
    await db.execute(
        update(WeeklySnapshot)
        .where(WeeklySnapshot.week_start_date == week_start)
        .values({req.field: col + 1, "updated_at": datetime.utcnow()})
    )
    await db.commit()
    return {"incremented": req.field}


@router.get("/snapshot/history", response_model=List[SnapshotOut])
async def get_snapshot_history(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(WeeklySnapshot)
        .order_by(WeeklySnapshot.week_start_date.desc())
        .limit(8)
    )
    return result.scalars().all()


@router.get("/alerts", response_model=List[AlertOut])
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    alerts: List[AlertOut] = []
    week_start = current_week_start()

    snap = await db.scalar(
        select(WeeklySnapshot).where(WeeklySnapshot.week_start_date == week_start)
    )
    messages_sent_this_week = snap.messages_sent if snap else 0

    # AL01: 3+ non-demo research reports this week AND 0 messages sent
    non_demo_research = await db.scalar(
        select(func.count())
        .select_from(ResearchReport)
        .where(
            ResearchReport.is_demo == False,
            ResearchReport.created_at >= datetime.combine(week_start, datetime.min.time()),
        )
    )
    if (non_demo_research or 0) >= 3 and messages_sent_this_week == 0:
        alerts.append(AlertOut(
            id="AL01",
            text=f"You have researched {non_demo_research} companies this week. No messages have been sent.",
            priority=1,
        ))

    # AL02: 5+ contacts with Not contacted status AND at least one draft exists
    not_contacted_count = await db.scalar(
        select(func.count()).select_from(Contact).where(
            Contact.outreach_status == "Not contacted"
        )
    )
    if (not_contacted_count or 0) >= 5:
        draft_exists = await db.scalar(
            select(func.count()).select_from(OutreachDraft).where(
                OutreachDraft.status == "draft"
            )
        )
        if draft_exists:
            alerts.append(AlertOut(
                id="AL02",
                text=f"{not_contacted_count} contacts have unsent drafts. Mark them sent or dismiss them.",
                priority=2,
            ))

    # AL03: Most recent sent draft has marked_sent_at > 48h ago AND no pending follow-up task for that contact
    recent_sent = await db.scalar(
        select(OutreachDraft)
        .where(OutreachDraft.status == "sent", OutreachDraft.marked_sent_at.isnot(None))
        .order_by(OutreachDraft.marked_sent_at.desc())
        .limit(1)
    )
    if recent_sent and recent_sent.marked_sent_at:
        cutoff = datetime.utcnow() - timedelta(hours=48)
        if recent_sent.marked_sent_at < cutoff and recent_sent.contact_id:
            pending_followup = await db.scalar(
                select(func.count()).select_from(Task).where(
                    Task.contact_id == recent_sent.contact_id,
                    Task.status == "pending",
                    Task.task_type == "followup",
                )
            )
            if not pending_followup:
                # Get contact name
                contact = await db.get(Contact, recent_sent.contact_id)
                company = await db.get(Company, recent_sent.company_id) if recent_sent.company_id else None
                contact_name = contact.name if contact else "contact"
                company_name = company.name if company else "their company"
                alerts.append(AlertOut(
                    id="AL03",
                    text=f"Follow-up overdue for {contact_name} at {company_name}.",
                    priority=3,
                ))

    # Sort by priority, max 3
    alerts.sort(key=lambda a: a.priority)
    return alerts[:3]


@router.put("/outreach/{draft_id}/mark-sent", response_model=MarkSentOut)
async def mark_draft_sent(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    draft = await db.get(OutreachDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status == "sent":
        raise HTTPException(status_code=400, detail="Draft already marked as sent")

    now = datetime.utcnow()
    followup_due = now + timedelta(hours=48)

    draft.status = OutreachDraftStatus.sent
    draft.marked_sent_at = now
    draft.followup_due_at = followup_due

    # Snapshot contact status before changing it
    contact = await db.get(Contact, draft.contact_id) if draft.contact_id else None
    if contact:
        draft.contact_status_after = contact.outreach_status
        # Update contact status if still at "Not contacted"
        if contact.outreach_status == OutreachStatus.not_contacted:
            contact.outreach_status = OutreachStatus.message_sent

    # Create follow-up task
    if draft.contact_id or draft.company_id:
        contact_name = contact.name if contact else "contact"
        company = await db.get(Company, draft.company_id) if draft.company_id else None
        company_name = company.name if company else "company"
        task = Task(
            company_id=draft.company_id,
            contact_id=draft.contact_id,
            description=f"Follow up with {contact_name} at {company_name}",
            due_date=followup_due,
            task_type="followup",
            status=TaskStatus.pending,
        )
        db.add(task)

    await db.commit()
    await db.refresh(draft)

    # Increment snapshot (messages_sent)
    week_start = current_week_start()
    await get_or_create_snapshot(db)
    await db.execute(
        update(WeeklySnapshot)
        .where(WeeklySnapshot.week_start_date == week_start)
        .values(
            messages_sent=WeeklySnapshot.messages_sent + 1,
            updated_at=datetime.utcnow(),
        )
    )
    await db.commit()

    return draft


@router.put("/briefs/{brief_id}/mark-sent")
async def mark_brief_sent(
    brief_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    brief = await db.get(SignalBrief, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    brief.is_sent = True
    await db.commit()

    # Increment briefs_sent
    week_start = current_week_start()
    await get_or_create_snapshot(db)
    await db.execute(
        update(WeeklySnapshot)
        .where(WeeklySnapshot.week_start_date == week_start)
        .values(briefs_sent=WeeklySnapshot.briefs_sent + 1, updated_at=datetime.utcnow())
    )
    await db.commit()
    return {"message": "Brief marked as sent", "brief_id": brief_id}


# ── Weekly Review ─────────────────────────────────────────────────────────────

async def get_or_create_review(db: AsyncSession) -> WeeklyReview:
    week_start = current_week_start()
    review = await db.scalar(
        select(WeeklyReview).where(WeeklyReview.week_start_date == week_start)
    )
    if not review:
        review = WeeklyReview(week_start_date=week_start)
        db.add(review)
        await db.commit()
        await db.refresh(review)
    return review


@router.get("/review/current", response_model=ReviewOut)
async def get_current_review(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    review = await get_or_create_review(db)
    return ReviewOut.from_orm(review)


@router.put("/review/current", response_model=ReviewOut)
async def update_review(
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    review = await get_or_create_review(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    review.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(review)
    return ReviewOut.from_orm(review)


@router.post("/review/generate", response_model=ReviewOut)
async def generate_review(
    req: ReviewGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    snap = await get_or_create_snapshot(db)
    review = await get_or_create_review(db)

    # Gather active company names
    companies_result = await db.execute(
        select(Company.name).where(Company.status == "active").limit(20)
    )
    active_companies = [row[0] for row in companies_result.all()]

    data = await ai_service.generate_weekly_review(
        snapshot={
            "messages_sent": snap.messages_sent,
            "replies_received": snap.replies_received,
            "companies_researched": snap.companies_researched,
        },
        what_worked=req.what_worked or review.what_worked or "",
        industry_response=req.industry_response or review.industry_response or "",
        active_companies=active_companies,
    )

    review.generated_targets = json.dumps(data.get("next_week_targets", []))
    review.generated_angle = data.get("improved_angle")
    review.top_followups = json.dumps(data.get("top_followups", []))
    review.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(review)
    return ReviewOut.from_orm(review)
