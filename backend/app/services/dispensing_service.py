import uuid as uuid_mod
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRN, GRNStatus
from app.models.dispensing import Dispensing
from app.models.material import Material
from app.models.stock_ledger import StockLedger, LedgerTxnType, LedgerStage
from app.schemas.dispensing import DispenseRequest
from app.services.audit_service import log_audit


async def get_dispense_queue(db: AsyncSession, item_code: str) -> dict:
    mat_result = await db.execute(
        select(Material).where(Material.item_code == item_code, Material.is_active == True)
    )
    material = mat_result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    result = await db.execute(
        select(GRN)
        .where(
            GRN.item_code == item_code,
            GRN.status == GRNStatus.APPROVED,
            GRN.material_issue_allowed == True,
            GRN.balance_qty > 0,
            GRN.is_active == True,
        )
        .order_by(GRN.exp_date.asc(), GRN.recv_date.asc())
    )
    grns = list(result.scalars().all())

    total_available = sum(g.balance_qty for g in grns)
    batches = [
        {
            "grn_id": g.id,
            "grn_number": g.grn_number,
            "batch_no": g.batch_no,
            "available_qty": g.balance_qty,
            "exp_date": g.exp_date,
            "recv_date": g.recv_date,
        }
        for g in grns
    ]
    return {
        "item_code": item_code,
        "item_name": material.item_name,
        "total_available_qty": total_available,
        "batches": batches,
    }


async def dispense(
    db: AsyncSession, payload: DispenseRequest, user_id: UUID,
) -> dict:
    if payload.grn_id:
        result = await db.execute(
            select(GRN).where(GRN.id == payload.grn_id, GRN.is_active == True)
        )
        grn = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(GRN)
            .where(
                GRN.item_code == payload.item_code,
                GRN.status == GRNStatus.APPROVED,
                GRN.material_issue_allowed == True,
                GRN.balance_qty > 0,
                GRN.is_active == True,
            )
            .order_by(GRN.exp_date.asc(), GRN.recv_date.asc())
            .limit(1)
        )
        grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No eligible GRN found")
    if grn.status != GRNStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GRN is not APPROVED")
    if not grn.material_issue_allowed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Material issue not allowed for this GRN")
    if grn.balance_qty < payload.qty_to_issue:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient balance: available {grn.balance_qty}, requested {payload.qty_to_issue}",
        )

    grn.balance_qty -= payload.qty_to_issue
    if grn.balance_qty == Decimal("0"):
        grn.status = GRNStatus.FULLY_DISPENSED
        grn.material_issue_allowed = False

    dispensing_id = uuid_mod.uuid4()
    record = Dispensing(
        id=dispensing_id,
        grn_id=grn.id,
        product_name=payload.product_name,
        product_batch_no=payload.product_batch_no,
        qty_issued=payload.qty_to_issue,
        issued_by=user_id,
        balance_qty_after=grn.balance_qty,
    )
    db.add(record)

    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=LedgerStage.APPROVED, txn_type=LedgerTxnType.OUT,
        qty_change=-payload.qty_to_issue, balance_after=grn.balance_qty,
        ref_type="dispensing", ref_id=dispensing_id, performed_by=user_id,
    ))

    await log_audit(
        db, "grn", grn.id, "DISPENSED",
        old_values={"balance_qty": str(grn.balance_qty + payload.qty_to_issue)},
        new_values={"balance_qty": str(grn.balance_qty), "qty_issued": str(payload.qty_to_issue)},
        performed_by=user_id,
    )

    await db.flush()
    return {
        "dispense_id": dispensing_id,
        "qty_issued": payload.qty_to_issue,
        "balance_qty_after": grn.balance_qty,
        "issued_by": user_id,
        "issued_at": record.issued_at,
    }
