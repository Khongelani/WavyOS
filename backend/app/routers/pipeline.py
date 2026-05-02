from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Company, PipelineStage
from app.schemas import CompanyOut, PipelineStageOut
from app.auth import get_current_user

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("", response_model=List[dict])
async def get_pipeline(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    stages_result = await db.execute(select(PipelineStage).order_by(PipelineStage.order_index))
    stages = stages_result.scalars().all()

    companies_result = await db.execute(
        select(Company).order_by(Company.updated_at.desc())
    )
    companies = companies_result.scalars().all()

    companies_by_stage = {}
    for company in companies:
        sid = company.pipeline_stage_id or 0
        if sid not in companies_by_stage:
            companies_by_stage[sid] = []
        companies_by_stage[sid].append({
            "id": company.id,
            "name": company.name,
            "industry": company.industry,
            "country": company.country,
            "updated_at": company.updated_at.isoformat() if company.updated_at else None,
            "pipeline_stage_id": company.pipeline_stage_id,
        })

    result = []
    for stage in stages:
        result.append({
            "stage": PipelineStageOut.model_validate(stage).model_dump(),
            "companies": companies_by_stage.get(stage.id, []),
        })

    # Include unassigned companies
    unassigned = companies_by_stage.get(0, [])
    if unassigned:
        result.insert(0, {
            "stage": {"id": 0, "name": "Unassigned", "order_index": 0, "color": "#64748B"},
            "companies": unassigned,
        })

    return result


@router.get("/stages", response_model=List[PipelineStageOut])
async def list_stages(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    result = await db.execute(select(PipelineStage).order_by(PipelineStage.order_index))
    return result.scalars().all()
