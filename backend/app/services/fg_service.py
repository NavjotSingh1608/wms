import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finished_goods import FinishedGoods, FGStatus
from app.schemas.finished_goods import FGCreate
from app.services.audit_service import log_audit


async def create_fg(
    db: AsyncSession, payload: FGCreate, user_id: UUID,
) -> FinishedGoods:
    fg = FinishedGoods(
        product_name=payload.product_name,
        product_code=payload.product_code,
        batch_no=payload.batch_no,
        mfg_date=payload.mfg_date,
        exp_date=payload.exp_date,
        total_qty=payload.total_qty,
        unit_of_measure=payload.unit_of_measure,
        remarks=payload.remarks,
        status=FGStatus.PENDING_QA_VERIFICATION,
        sent_by=user_id,
    )
    db.add(fg)
    await db.flush()
    return fg


async def list_fg(
    db: AsyncSession, page: int = 1, per_page: int = 50,
) -> dict:
    base_filter = [FinishedGoods.is_active == True, FinishedGoods.deleted_at == None]
    total = (
        await db.execute(select(func.count()).select_from(FinishedGoods).where(*base_filter))
    ).scalar() or 0

    items = list(
        (
            await db.execute(
                select(FinishedGoods)
                .where(*base_filter)
                .order_by(FinishedGoods.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        ).scalars().all()
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 0,
    }


async def _get_fg(db: AsyncSession, fg_id: UUID) -> FinishedGoods:
    result = await db.execute(
        select(FinishedGoods).where(FinishedGoods.id == fg_id, FinishedGoods.is_active == True)
    )
    fg = result.scalar_one_or_none()
    if not fg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finished good not found")
    return fg


async def qa_verify(db: AsyncSession, fg_id: UUID, user_id: UUID) -> FinishedGoods:
    fg = await _get_fg(db, fg_id)
    if fg.status != FGStatus.PENDING_QA_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"FG must be PENDING_QA_VERIFICATION, currently {fg.status.value}",
        )
    old_status = fg.status.value
    fg.status = FGStatus.QA_VERIFIED
    fg.qa_verified_by = user_id
    fg.qa_verified_at = datetime.now(timezone.utc)
    fg.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_audit(
        db, "finished_goods", fg.id, "QA_VERIFIED",
        old_values={"status": old_status},
        new_values={"status": fg.status.value},
        performed_by=user_id,
    )
    return fg


async def qa_approve(db: AsyncSession, fg_id: UUID, user_id: UUID) -> FinishedGoods:
    fg = await _get_fg(db, fg_id)
    if fg.status != FGStatus.QA_VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"FG must be QA_VERIFIED, currently {fg.status.value}",
        )
    old_status = fg.status.value
    fg.status = FGStatus.QA_APPROVED
    fg.qa_approved_by = user_id
    fg.qa_approved_at = datetime.now(timezone.utc)
    fg.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_audit(
        db, "finished_goods", fg.id, "QA_APPROVED",
        old_values={"status": old_status},
        new_values={"status": fg.status.value},
        performed_by=user_id,
    )
    return fg


async def qa_reject(
    db: AsyncSession, fg_id: UUID, reason: str, user_id: UUID,
) -> FinishedGoods:
    fg = await _get_fg(db, fg_id)
    if fg.status not in (FGStatus.PENDING_QA_VERIFICATION, FGStatus.QA_VERIFIED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"FG cannot be rejected in status {fg.status.value}",
        )
    old_status = fg.status.value
    fg.status = FGStatus.QA_REJECTED
    fg.qa_rejection_reason = reason
    fg.qa_approved_by = user_id
    fg.qa_approved_at = datetime.now(timezone.utc)
    fg.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_audit(
        db, "finished_goods", fg.id, "QA_REJECTED",
        old_values={"status": old_status},
        new_values={"status": fg.status.value, "reason": reason},
        performed_by=user_id,
    )
    return fg


async def receive_fg(db: AsyncSession, fg_id: UUID, user_id: UUID) -> FinishedGoods:
    fg = await _get_fg(db, fg_id)
    if fg.status != FGStatus.QA_APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"FG must be QA_APPROVED, currently {fg.status.value}",
        )
    old_status = fg.status.value
    fg.status = FGStatus.WH_RECEIVED
    fg.wh_received_by = user_id
    fg.wh_received_at = datetime.now(timezone.utc)
    fg.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_audit(
        db, "finished_goods", fg.id, "WH_RECEIVED",
        old_values={"status": old_status},
        new_values={"status": fg.status.value},
        performed_by=user_id,
    )
    return fg


async def dispatch_fg(db: AsyncSession, fg_id: UUID, user_id: UUID) -> FinishedGoods:
    fg = await _get_fg(db, fg_id)
    if fg.status != FGStatus.WH_RECEIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"FG must be WH_RECEIVED, currently {fg.status.value}",
        )
    old_status = fg.status.value
    fg.status = FGStatus.DISPATCHED
    fg.dispatched_by = user_id
    fg.dispatched_at = datetime.now(timezone.utc)
    fg.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_audit(
        db, "finished_goods", fg.id, "DISPATCHED",
        old_values={"status": old_status},
        new_values={"status": fg.status.value},
        performed_by=user_id,
    )
    return fg
