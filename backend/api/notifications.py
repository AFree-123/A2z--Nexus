"""
Notifications router.

GET   /api/notifications          ?user_id=
PATCH /api/notifications/{id}/read
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import get_db
from database.models import Notification
from models.schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    user_id: str = Query(default="default-user"),
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.read == False)  # noqa: E712
    stmt = stmt.order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    from fastapi import HTTPException
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse.model_validate(notification)
