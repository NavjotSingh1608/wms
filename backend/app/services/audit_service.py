import math
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit(
    db: AsyncSession,
    entity_type: str,
    entity_id: UUID,
    action: str,
    old_values: dict | None,
    new_values: dict | None,
    performed_by: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        performed_by=performed_by,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_audit_trail(
    db: AsyncSession,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    query = select(AuditLog)
    count_q = select(func.count()).select_from(AuditLog)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_q = count_q.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
        count_q = count_q.where(AuditLog.entity_id == entity_id)

    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(AuditLog.performed_at.desc()).offset((page - 1) * per_page).limit(per_page)
    items = list((await db.execute(query)).scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 0,
    }
