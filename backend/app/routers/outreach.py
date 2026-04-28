from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Contact, Company, SignalBrief, OutreachDraft
from app.schemas import OutreachGenerateRequest, OutreachDraftOut
from app.auth import get_current_user
from app import ai_service
from app.schemas import _parse_json_field

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/generate", response_model=OutreachDraftOut, status_code=status.HTTP_201_CREATED)
async def generate_outreach(
    req: OutreachGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    contact = await db.get(Contact, req.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    company = await db.get(Company, req.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    brief_data = {}
    if req.brief_id:
        brief = await db.get(SignalBrief, req.brief_id)
        if brief:
            brief_data = {
                "executive_signal": brief.executive_signal,
                "conversation_opener": brief.conversation_opener,
                "suggested_action": brief.suggested_action,
            }

    data = await ai_service.generate_outreach(
        contact_name=contact.name,
        contact_role=contact.role or "Executive",
        company_name=company.name,
        brief_data=brief_data,
        tone=req.tone or "professional",
    )

    draft = OutreachDraft(
        contact_id=req.contact_id,
        company_id=req.company_id,
        brief_id=req.brief_id,
        linkedin_message=data.get("linkedin_message"),
        email_subject=data.get("email_subject"),
        email_body=data.get("email_body"),
        followup_message=data.get("followup_message"),
        gatekeeper_version=data.get("gatekeeper_version"),
        technical_validator_version=data.get("technical_validator_version"),
        is_demo=data.get("is_demo", False),
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return draft
