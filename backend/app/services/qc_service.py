import uuid as uuid_mod
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRN, GRNStatus
from app.models.qc import QCSampling, QCDecision, QCDecisionType
from app.models.retesting import RetestingCycle
from app.models.stock_ledger import StockLedger, LedgerTxnType, LedgerStage
from app.schemas.qc import SamplingCreate, DecisionCreate
from app.services.audit_service import log_audit


async def create_sampling(
    db: AsyncSession, payload: SamplingCreate, user_id: UUID,
) -> QCSampling:
    result = await db.execute(
        select(GRN).where(GRN.id == payload.grn_id, GRN.is_active == True)
    )
    grn = result.scalar_one_or_none()
    if not grn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")

    allowed = {GRNStatus.QUARANTINE, GRNStatus.QUARANTINE_RETESTING}
    if grn.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GRN status must be QUARANTINE or QUARANTINE_RETESTING, currently {grn.status.value}",
        )

    sampling_id = uuid_mod.uuid4()
    sampling = QCSampling(
        id=sampling_id,
        grn_id=grn.id,
        ar_number=payload.ar_number,
        sample_qty=payload.sample_qty,
        sampled_by=user_id,
        notes=payload.notes,
    )
    db.add(sampling)

    old_status = grn.status.value
    from_stage = LedgerStage.QUARANTINE if grn.status == GRNStatus.QUARANTINE else LedgerStage.QUARANTINE_RETESTING
    grn.status = GRNStatus.UNDER_TEST
    grn.updated_by = user_id
    grn.updated_at = datetime.now(timezone.utc)

    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=from_stage, txn_type=LedgerTxnType.OUT,
        qty_change=-grn.balance_qty, balance_after=grn.balance_qty,
        ref_type="qc_sampling", ref_id=sampling_id, performed_by=user_id,
    ))
    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=LedgerStage.UNDER_TEST, txn_type=LedgerTxnType.IN,
        qty_change=grn.balance_qty, balance_after=grn.balance_qty,
        ref_type="qc_sampling", ref_id=sampling_id, performed_by=user_id,
    ))

    await log_audit(
        db, "grn", grn.id, "QC_SAMPLING",
        old_values={"status": old_status},
        new_values={"status": GRNStatus.UNDER_TEST.value, "ar_number": payload.ar_number},
        performed_by=user_id,
    )

    await db.flush()
    return sampling


async def create_decision(
    db: AsyncSession, payload: DecisionCreate, user_id: UUID,
) -> QCDecision:
    result = await db.execute(
        select(GRN).where(GRN.id == payload.grn_id, GRN.is_active == True)
    )
    grn = result.scalar_one_or_none()
    if not grn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")
    if grn.status != GRNStatus.UNDER_TEST:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GRN status must be UNDER_TEST, currently {grn.status.value}",
        )

    sampling_result = await db.execute(
        select(QCSampling)
        .where(QCSampling.grn_id == grn.id)
        .order_by(QCSampling.created_at.desc())
        .limit(1)
    )
    sampling = sampling_result.scalar_one_or_none()
    if not sampling:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No QC sampling found for this GRN",
        )

    cycle_result = await db.execute(
        select(func.count()).select_from(RetestingCycle).where(RetestingCycle.grn_id == grn.id)
    )
    cycle_no = cycle_result.scalar() or 0

    decision_type = QCDecisionType(payload.decision)
    decision_id = uuid_mod.uuid4()
    decision = QCDecision(
        id=decision_id,
        grn_id=grn.id,
        sampling_id=sampling.id,
        decision=decision_type,
        test_remarks=payload.test_remarks,
        rejection_reason=payload.rejection_reason,
        retesting_date=payload.retesting_date,
        decided_by=user_id,
        retest_cycle_no=cycle_no,
    )
    db.add(decision)

    old_status = grn.status.value
    if decision_type == QCDecisionType.APPROVED:
        grn.status = GRNStatus.APPROVED
        grn.material_issue_allowed = True
        grn.retesting_date = payload.retesting_date
        new_stage = LedgerStage.APPROVED
    else:
        grn.status = GRNStatus.REJECTED
        grn.material_issue_allowed = False
        new_stage = LedgerStage.REJECTED

    grn.updated_by = user_id
    grn.updated_at = datetime.now(timezone.utc)

    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=LedgerStage.UNDER_TEST, txn_type=LedgerTxnType.OUT,
        qty_change=-grn.balance_qty, balance_after=grn.balance_qty,
        ref_type="qc_decision", ref_id=decision_id, performed_by=user_id,
    ))
    db.add(StockLedger(
        item_code=grn.item_code, batch_no=grn.batch_no, grn_id=grn.id,
        stage=new_stage, txn_type=LedgerTxnType.IN,
        qty_change=grn.balance_qty, balance_after=grn.balance_qty,
        ref_type="qc_decision", ref_id=decision_id, performed_by=user_id,
    ))

    await log_audit(
        db, "grn", grn.id, f"QC_{payload.decision}",
        old_values={"status": old_status},
        new_values={"status": grn.status.value, "decision": payload.decision},
        performed_by=user_id,
    )

    await db.flush()
    return decision
