from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import Company, PipelineStage, Task
from app.auth import get_current_user
from app.routers.execution import current_week_start

router = APIRouter(prefix="/sprint", tags=["sprint"])


class SprintCompanyOut(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None
    pipeline_stage_id: Optional[int] = None
    pipeline_stage_name: Optional[str] = None
    pipeline_stage_color: Optional[str] = None
    days_in_stage: int
    last_task_due: Optional[datetime] = None
    needs_action: bool  # True if no stage change in 7+ days
    updated_at: datetime
    model_config = {"from_attributes": True}


class SprintSummaryOut(BaseModel):
    active_companies: int
    need_action: int
    moved_forward_this_week: int
    companies: List[SprintCompanyOut]


@router.get("/companies", response_model=SprintSummaryOut)
async def get_sprint_companies(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    # Get all active companies (not Won/Lost — stage 9/10)
    stages_result = await db.execute(select(PipelineStage))
    all_stages = {s.id: s for s in stages_result.scalars().all()}

    # Won = order_index 9, Lost = order_index 10
    excluded_stage_ids = {
        s.id for s in all_stages.values() if s.order_index >= 9
    }

    companies_result = await db.execute(
        select(Company)
        .where(
            Company.status == "active",
            ~Company.pipeline_stage_id.in_(excluded_stage_ids)
            if excluded_stage_ids else True,
        )
        .order_by(Company.pipeline_stage_id.asc().nulls_last(), Company.updated_at.asc())
    )
    companies = companies_result.scalars().all()

    now = datetime.utcnow()
    week_start = datetime.combine(current_week_start(), datetime.min.time())
    seven_days_ago = now - timedelta(days=7)

    result_companies: List[SprintCompanyOut] = []
    need_action_count = 0
    moved_forward_count = 0

    for company in companies:
        # Calculate days in current stage
        days_in_stage = (now - company.updated_at).days

        # Last pending task due date
        task_result = await db.scalar(
            select(Task.due_date)
            .where(Task.company_id == company.id, Task.status == "pending")
            .order_by(Task.due_date.asc().nulls_last())
            .limit(1)
        )

        needs_action = company.updated_at < seven_days_ago
        if needs_action:
            need_action_count += 1

        # Moved forward this week = updated_at >= Monday of current week
        if company.updated_at >= week_start:
            moved_forward_count += 1

        stage = all_stages.get(company.pipeline_stage_id) if company.pipeline_stage_id else None

        result_companies.append(SprintCompanyOut(
            id=company.id,
            name=company.name,
            industry=company.industry,
            country=company.country,
            pipeline_stage_id=company.pipeline_stage_id,
            pipeline_stage_name=stage.name if stage else None,
            pipeline_stage_color=stage.color if stage else None,
            days_in_stage=days_in_stage,
            last_task_due=task_result,
            needs_action=needs_action,
            updated_at=company.updated_at,
        ))

    return SprintSummaryOut(
        active_companies=len(result_companies),
        need_action=need_action_count,
        moved_forward_this_week=moved_forward_count,
        companies=result_companies,
    )
