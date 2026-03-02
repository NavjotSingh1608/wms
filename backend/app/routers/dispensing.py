from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.dispensing import DispenseRequest, DispenseOut, DispenseQueueOut
from app.services import dispensing_service

router = APIRouter()


@router.get("/dispensing/queue/{item_code}", response_model=DispenseQueueOut)
async def get_dispense_queue(
    item_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("material:issue")),
):
    return await dispensing_service.get_dispense_queue(db, item_code)


@router.post("/dispensing", response_model=DispenseOut, status_code=status.HTTP_201_CREATED)
async def dispense(
    payload: DispenseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("material:issue")),
):
    return await dispensing_service.dispense(db, payload, current_user.id)
