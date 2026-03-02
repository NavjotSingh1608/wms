from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.grade_transfer import TransferRequest, TransferOut
from app.services import grade_transfer_service

router = APIRouter()


class RejectBody(BaseModel):
    remarks: str | None = None


@router.post(
    "/grade-transfers",
    response_model=TransferOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_transfer(
    payload: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade:transfer_request")),
):
    t = await grade_transfer_service.create_transfer_request(db, payload, current_user.id)
    return _to_out(t)


@router.put("/grade-transfers/{transfer_id}/approve", response_model=TransferOut)
async def approve_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade:change")),
):
    t = await grade_transfer_service.approve_transfer(db, transfer_id, current_user.id)
    return _to_out(t)


@router.put("/grade-transfers/{transfer_id}/reject", response_model=TransferOut)
async def reject_transfer(
    transfer_id: UUID,
    body: RejectBody | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("grade:change")),
):
    remarks = body.remarks if body else None
    t = await grade_transfer_service.reject_transfer(db, transfer_id, current_user.id, remarks)
    return _to_out(t)


def _to_out(t) -> dict:
    return {
        "transfer_id": t.id,
        "grn_id": t.grn_id,
        "from_item_code": t.from_item_code,
        "to_item_code": t.to_item_code,
        "status": t.status.value if hasattr(t.status, "value") else t.status,
        "requested_by": t.requested_by,
        "requested_at": t.requested_at,
        "approved_by": t.approved_by,
        "approved_at": t.approved_at,
        "new_grn_id": t.new_grn_id,
    }
