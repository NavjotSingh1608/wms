from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.services import audit_service

router = APIRouter()


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    old_values: dict | None = None
    new_values: dict | None = None
    performed_by: UUID
    ip_address: str | None = None
    user_agent: str | None = None
    performed_at: datetime


class AuditListOut(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    per_page: int
    pages: int


@router.get("/audit", response_model=AuditListOut)
async def get_audit_trail(
    entity_type: str | None = Query(None),
    entity_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("audit:view")),
):
    return await audit_service.get_audit_trail(db, entity_type, entity_id, page, per_page)
