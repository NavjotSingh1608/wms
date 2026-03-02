from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.finished_goods import FGCreate, FGOut, FGListOut
from app.services import fg_service

router = APIRouter()


class RejectReason(BaseModel):
    reason: str


@router.post("/fg", response_model=FGOut, status_code=status.HTTP_201_CREATED)
async def create_fg(
    payload: FGCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fg:send_to_warehouse")),
):
    return await fg_service.create_fg(db, payload, current_user.id)


@router.get("/fg", response_model=FGListOut)
async def list_fg(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("stock:view")),
):
    return await fg_service.list_fg(db, page, per_page)


@router.put("/fg/{fg_id}/qa-verify", response_model=FGOut)
async def qa_verify(
    fg_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fg:qa_approve")),
):
    return await fg_service.qa_verify(db, fg_id, current_user.id)


@router.put("/fg/{fg_id}/qa-approve", response_model=FGOut)
async def qa_approve(
    fg_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fg:qa_approve")),
):
    return await fg_service.qa_approve(db, fg_id, current_user.id)


@router.put("/fg/{fg_id}/qa-reject", response_model=FGOut)
async def qa_reject(
    fg_id: UUID,
    body: RejectReason,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fg:qa_approve")),
):
    return await fg_service.qa_reject(db, fg_id, body.reason, current_user.id)


@router.put("/fg/{fg_id}/receive", response_model=FGOut)
async def receive_fg(
    fg_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fg:receive")),
):
    return await fg_service.receive_fg(db, fg_id, current_user.id)


@router.put("/fg/{fg_id}/dispatch", response_model=FGOut)
async def dispatch_fg(
    fg_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("fg:dispatch")),
):
    return await fg_service.dispatch_fg(db, fg_id, current_user.id)
