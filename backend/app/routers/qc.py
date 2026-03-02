from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.qc import SamplingCreate, SamplingOut, DecisionCreate, DecisionOut
from app.services import qc_service

router = APIRouter()


@router.post("/qc/sampling", response_model=SamplingOut, status_code=status.HTTP_201_CREATED)
async def create_sampling(
    payload: SamplingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("qc:sampling")),
):
    return await qc_service.create_sampling(db, payload, current_user.id)


@router.post("/qc/decision", response_model=DecisionOut, status_code=status.HTTP_201_CREATED)
async def create_decision(
    payload: DecisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("qc:approve")),
):
    return await qc_service.create_decision(db, payload, current_user.id)
