from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional

from app.database import get_db
from app.models import Contact, WeeklySnapshot
from app.schemas import ContactCreate, ContactUpdate, ContactOut
from app.auth import get_current_user
from app.routers.execution import get_or_create_snapshot, current_week_start

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=List[ContactOut])
async def list_contacts(
    company_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    q = select(Contact)
    if company_id:
        q = q.where(Contact.company_id == company_id)
    q = q.order_by(Contact.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    contact = Contact(**data.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    prev_status = contact.outreach_status
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await db.commit()
    await db.refresh(contact)

    # Auto-increment execution snapshot based on status transitions
    new_status = contact.outreach_status
    if prev_status != new_status:
        week_start = current_week_start()
        await get_or_create_snapshot(db)
        if new_status == "Replied":
            await db.execute(
                update(WeeklySnapshot)
                .where(WeeklySnapshot.week_start_date == week_start)
                .values(replies_received=WeeklySnapshot.replies_received + 1, updated_at=datetime.utcnow())
            )
            await db.commit()
        elif new_status == "Meeting booked":
            await db.execute(
                update(WeeklySnapshot)
                .where(WeeklySnapshot.week_start_date == week_start)
                .values(calls_requested=WeeklySnapshot.calls_requested + 1, updated_at=datetime.utcnow())
            )
            await db.commit()

    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
    await db.commit()
