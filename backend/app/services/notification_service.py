import math
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    type: NotificationType,
    title: str,
    body: str,
    ref_type: str | None = None,
    ref_id: UUID | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        ref_type=ref_type,
        ref_id=ref_id,
    )
    db.add(notif)
    await db.flush()
    return notif


async def get_notifications(
    db: AsyncSession,
    user_id: UUID,
    unread_only: bool = False,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    query = select(Notification).where(Notification.user_id == user_id)
    count_q = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)

    if unread_only:
        query = query.where(Notification.is_read == False)
        count_q = count_q.where(Notification.is_read == False)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Notification.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    items = list((await db.execute(query)).scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 0,
    }


async def mark_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> Notification:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.flush()
    return notif
