import uuid as uuid_mod
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRN, GRNStatus
from app.models.grade_transfer import GradeTransfer, TransferStatus
from app.models.material import Material
from app.models.stock_ledger import StockLedger, LedgerTxnType, LedgerStage
from app.models.qr_label import QRLabel, LabelType
from app.schemas.grade_transfer import TransferRequest
from app.services.audit_service import log_audit


async def _next_grn_number(db: AsyncSession) -> str:
    """Reuse numbering logic for transfer-created GRNs."""
    from app.services.grn_service import _next_grn_number as _gen
    return await _gen(db)


async def create_transfer_request(
    db: AsyncSession, payload: TransferRequest, user_id: UUID,
) -> GradeTransfer:
    result = await db.execute(
        select(GRN).where(GRN.id == payload.grn_id, GRN.is_active == True)
    )
    grn = result.scalar_one_or_none()
    if not grn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")
    if grn.status not in (GRNStatus.APPROVED, GRNStatus.APPROVED_BP_USP):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="GRN must be APPROVED for grade transfer",
        )

    to_mat = await db.execute(
        select(Material).where(Material.item_code == payload.to_item_code, Material.is_active == True)
    )
    if not to_mat.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target material not found")

    grn.status = GRNStatus.BLOCKED_PENDING_QC_RELEASE
    grn.material_issue_allowed = False
    grn.updated_by = user_id
    grn.updated_at = datetime.now(timezone.utc)

    transfer = GradeTransfer(
        grn_id=grn.id,
        from_item_code=payload.from_item_code,
        to_item_code=payload.to_item_code,
        ar_number_ref=payload.ar_number,
        requested_by=user_id,
        status=TransferStatus.PENDING,
    )
    db.add(transfer)
    await db.flush()

    await log_audit(
        db, "grade_transfer", transfer.id, "TRANSFER_REQUESTED",
        old_values={"status": "APPROVED"},
        new_values={"status": "BLOCKED_PENDING_QC_RELEASE", "to_item_code": payload.to_item_code},
        performed_by=user_id,
    )
    return transfer


async def approve_transfer(
    db: AsyncSession, transfer_id: UUID, user_id: UUID,
) -> GradeTransfer:
    result = await db.execute(
        select(GradeTransfer).where(GradeTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    if transfer.status != TransferStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transfer is not PENDING")

    grn_result = await db.execute(select(GRN).where(GRN.id == transfer.grn_id))
    original_grn = grn_result.scalar_one()
    original_balance = original_grn.balance_qty

    new_grn_number = await _next_grn_number(db)
    new_grn = GRN(
        grn_number=new_grn_number,
        item_code=transfer.to_item_code,
        batch_no=original_grn.batch_no,
        supplier_name=original_grn.supplier_name,
        manufacturer_name=original_grn.manufacturer_name,
        total_recv_qty=original_balance,
        container_qty=original_grn.container_qty,
        containers_count=original_grn.containers_count,
        pack_size_description=original_grn.pack_size_description,
        unit_of_measure=original_grn.unit_of_measure,
        recv_date=original_grn.recv_date,
        mfg_date=original_grn.mfg_date,
        exp_date=original_grn.exp_date,
        grade=original_grn.grade,
        status=GRNStatus.APPROVED_BP_USP,
        balance_qty=original_balance,
        material_issue_allowed=True,
        created_by=user_id,
    )
    db.add(new_grn)

    original_grn.balance_qty = 0
    original_grn.status = GRNStatus.FULLY_DISPENSED
    original_grn.material_issue_allowed = False
    original_grn.updated_by = user_id
    original_grn.updated_at = datetime.now(timezone.utc)

    await db.flush()

    db.add(StockLedger(
        item_code=original_grn.item_code, batch_no=original_grn.batch_no,
        grn_id=original_grn.id,
        stage=LedgerStage.APPROVED, txn_type=LedgerTxnType.TRANSFER_OUT,
        qty_change=-original_balance, balance_after=0,
        ref_type="grade_transfer", ref_id=transfer.id, performed_by=user_id,
    ))
    db.add(StockLedger(
        item_code=new_grn.item_code, batch_no=new_grn.batch_no,
        grn_id=new_grn.id,
        stage=LedgerStage.APPROVED, txn_type=LedgerTxnType.TRANSFER_IN,
        qty_change=original_balance, balance_after=original_balance,
        ref_type="grade_transfer", ref_id=transfer.id, performed_by=user_id,
    ))

    qr_label = QRLabel(
        grn_id=new_grn.id,
        label_type=LabelType.QUARANTINE,
        qr_data=f"GRN:{new_grn.grn_number}|ITEM:{new_grn.item_code}|BATCH:{new_grn.batch_no}",
        generated_by=user_id,
    )
    db.add(qr_label)

    transfer.status = TransferStatus.APPROVED
    transfer.approved_by = user_id
    transfer.approved_at = datetime.now(timezone.utc)
    transfer.new_grn_id = new_grn.id

    await db.flush()

    await log_audit(
        db, "grade_transfer", transfer.id, "TRANSFER_APPROVED",
        old_values={"status": "PENDING"},
        new_values={"status": "APPROVED", "new_grn_id": str(new_grn.id)},
        performed_by=user_id,
    )
    return transfer


async def reject_transfer(
    db: AsyncSession, transfer_id: UUID, user_id: UUID, remarks: str | None = None,
) -> GradeTransfer:
    result = await db.execute(
        select(GradeTransfer).where(GradeTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")
    if transfer.status != TransferStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transfer is not PENDING")

    grn_result = await db.execute(select(GRN).where(GRN.id == transfer.grn_id))
    grn = grn_result.scalar_one()
    grn.status = GRNStatus.APPROVED
    grn.material_issue_allowed = True
    grn.updated_by = user_id
    grn.updated_at = datetime.now(timezone.utc)

    transfer.status = TransferStatus.REJECTED
    transfer.rejection_remarks = remarks
    transfer.approved_by = user_id
    transfer.approved_at = datetime.now(timezone.utc)

    await db.flush()

    await log_audit(
        db, "grade_transfer", transfer.id, "TRANSFER_REJECTED",
        old_values={"status": "PENDING"},
        new_values={"status": "REJECTED"},
        performed_by=user_id,
    )
    return transfer
