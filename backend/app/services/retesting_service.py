import math
from datetime import datetime, timezone, date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRN, GRNStatus
from app.models.retesting import RetestingCycle
from app.models.stock_ledger import StockLedger, LedgerTxnType, LedgerStage
from app.services.audit_service import log_audit


async def initiate_retest(
    db: AsyncSession, grn_id: UUID, user_id: UUID,
) -> RetestingCycle:
    result = await db.execute(
        select(GRN).where(GRN.id == grn_id, GRN.is_active == True)
    )
    grn = result.scalar_one_or_none()
    if not grn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")
    if grn.status != GRNStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GRN must be APPROVED to initiate retest, currently {grn.status.value}",
        )

    max_cycle = (
        await db.execute(
            select(func.max(RetestingCycle.cycle_no)).where(RetestingCycle.grn_id == grn.id)
        )
    ).scalar() or 0

    old_status = grn.status.value
    grn.status = GRNStatus.QUARANTINE_RETESTING
    grn.material_issue_allowed = False
    grn.updated_by = user_id
    grn.updated_at = datetime.now(timezone.utc)

    cycle = RetestingCycle(
        grn_id=grn.id,
        cycle_no=max_cycle + 1,
        initiated_by=user_id,
    )
    db.add(cycle)

    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=LedgerStage.APPROVED, txn_type=LedgerTxnType.OUT,
        qty_change=-grn.balance_qty, balance_after=grn.balance_qty,
        ref_type="retesting", ref_id=grn.id, performed_by=user_id,
    ))
    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=LedgerStage.QUARANTINE_RETESTING, txn_type=LedgerTxnType.IN,
        qty_change=grn.balance_qty, balance_after=grn.balance_qty,
        ref_type="retesting", ref_id=grn.id, performed_by=user_id,
    ))

    await log_audit(
        db, "grn", grn.id, "RETEST_INITIATED",
        old_values={"status": old_status},
        new_values={"status": GRNStatus.QUARANTINE_RETESTING.value, "cycle_no": max_cycle + 1},
        performed_by=user_id,
    )

    await db.flush()
    return cycle


async def get_pending_retests(
    db: AsyncSession, page: int = 1, per_page: int = 50,
) -> dict:
    today = date.today()
    base_filter = [
        GRN.is_active == True,
        GRN.deleted_at == None,
        (
            (GRN.status == GRNStatus.QUARANTINE_RETESTING)
            | (
                (GRN.status == GRNStatus.APPROVED)
                & (GRN.retesting_date != None)
                & (GRN.retesting_date <= today)
            )
        ),
    ]

    total = (
        await db.execute(select(func.count()).select_from(GRN).where(*base_filter))
    ).scalar() or 0

    items = list(
        (
            await db.execute(
                select(GRN).where(*base_filter)
                .order_by(GRN.retesting_date.asc().nulls_last())
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
