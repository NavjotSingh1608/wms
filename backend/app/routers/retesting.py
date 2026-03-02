from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.grn import GRNOut, GRNListOut
from app.services import retesting_service

router = APIRouter()


class RetestInitiate(BaseModel):
    grn_id: UUID


class RetestCycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_id: UUID
    cycle_no: int
    initiated_by: UUID


@router.post(
    "/retesting/initiate",
    response_model=RetestCycleOut,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_retest(
    payload: RetestInitiate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("retest:initiate")),
):
    return await retesting_service.initiate_retest(db, payload.grn_id, current_user.id)


@router.get("/retesting/pending", response_model=GRNListOut)
async def get_pending_retests(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("stock:view")),
):
    return await retesting_service.get_pending_retests(db, page, per_page)
