from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.grn import GRNCreate, GRNOut, GRNListOut, GRNRevise, RackUpdate
from app.services import grn_service

router = APIRouter()


@router.post("/grn", response_model=GRNOut, status_code=status.HTTP_201_CREATED)
async def create_grn(
    payload: GRNCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grn:create")),
):
    grn = await grn_service.create_grn(db, payload, current_user.id)
    return grn


@router.get("/grn", response_model=GRNListOut)
async def list_grns(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("stock:view")),
):
    return await grn_service.list_grns(db, page, per_page, status_filter)


@router.get("/grn/{grn_id}", response_model=GRNOut)
async def get_grn(
    grn_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("stock:view")),
):
    return await grn_service.get_grn(db, grn_id)


@router.put("/grn/{grn_id}/rack", response_model=GRNOut)
async def update_rack(
    grn_id: UUID,
    payload: RackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("material:update_rack")),
):
    return await grn_service.update_rack(db, grn_id, payload.rack_no, current_user.id)


@router.post("/grn/{grn_id}/revise", response_model=GRNOut, status_code=status.HTTP_201_CREATED)
async def revise_grn(
    grn_id: UUID,
    payload: GRNRevise,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grn:revise")),
):
    return await grn_service.revise_grn(db, grn_id, payload, current_user.id)
