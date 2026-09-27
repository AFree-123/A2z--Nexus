"""
Reminders router.

POST /api/reminders
GET  /api/reminders   ?user_id=
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.models import Reminder
from models.schemas import ReminderCreate, ReminderResponse

router = APIRouter(prefix="/reminders", tags=["reminders"])


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.post("", response_model=ReminderResponse, status_code=201)
async def create_reminder(
    payload: ReminderCreate,
    db: AsyncSession = Depends(get_db),
) -> ReminderResponse:
    from api.projects import _ensure_user  # avoid circular at module level
    await _ensure_user(payload.user_id, db)

    reminder = Reminder(
        id=str(uuid.uuid4()),
        user_id=payload.user_id,
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description or "",
        due_date=payload.due_date,
        created_at=_now(),
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.model_validate(reminder)


@router.get("", response_model=list[ReminderResponse])
async def list_reminders(
    user_id: str = Query(default="default-user"),
    db: AsyncSession = Depends(get_db),
) -> list[ReminderResponse]:
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user_id)
        .order_by(Reminder.created_at.desc())
    )
    reminders = result.scalars().all()
    return [ReminderResponse.model_validate(r) for r in reminders]

@router.post("/{reminder_id}/calendar")
async def add_reminder_to_google_calendar(reminder_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Create the reminder in the connected user's Google Calendar."""
    from sqlalchemy import select
    from database.models import OAuthCredential
    from integrations.google_calendar import create_event

    reminder = await db.get(Reminder, reminder_id)
    if reminder is None:
        from fastapi import HTTPException
        raise HTTPException(404, "Reminder not found")
    result = await db.execute(select(OAuthCredential).where(OAuthCredential.user_id == reminder.user_id, OAuthCredential.provider == "google"))
    credential = result.scalar_one_or_none()
    if credential is None:
        from fastapi import HTTPException
        raise HTTPException(503, "Connect Google first with Continue with Google to enable Calendar reminders.")
    try:
        event = await create_event(credential.access_token, reminder.title, reminder.description, reminder.due_date or "")
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(502, f"Google Calendar event creation failed: {str(exc)[:300]}") from exc
    reminder.calendar_event_id = event.get("id")
    reminder.confirmed = True
    await db.commit()
    return {"success": True, "reminder_id": reminder.id, "calendar_event_id": reminder.calendar_event_id, "html_link": event.get("htmlLink")}
