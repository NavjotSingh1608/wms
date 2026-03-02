from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.grn import GRN
from app.models.material import Material
from app.models.qc import QCSampling, QCDecision
from app.models.dispensing import Dispensing

router = APIRouter()


@router.get("/qr/scan/{grn_id}")
async def scan_qr(grn_id: UUID, db: AsyncSession = Depends(get_db)):
    """Public endpoint — no auth required. Returns full GRN details."""
    result = await db.execute(select(GRN).where(GRN.id == grn_id, GRN.is_active == True))
    grn = result.scalar_one_or_none()
    if not grn:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")

    mat_result = await db.execute(
        select(Material).where(Material.item_code == grn.item_code)
    )
    material = mat_result.scalar_one_or_none()

    sampling_result = await db.execute(
        select(QCSampling)
        .where(QCSampling.grn_id == grn.id)
        .order_by(QCSampling.created_at.desc())
        .limit(1)
    )
    sampling = sampling_result.scalar_one_or_none()

    decision_result = await db.execute(
        select(QCDecision)
        .where(QCDecision.grn_id == grn.id)
        .order_by(QCDecision.decided_at.desc())
        .limit(1)
    )
    decision = decision_result.scalar_one_or_none()

    dispensed_result = await db.execute(
        select(
            func.coalesce(func.sum(Dispensing.qty_issued), 0),
            func.count(Dispensing.id),
        ).where(Dispensing.grn_id == grn.id)
    )
    dispensed_row = dispensed_result.one()

    return {
        "grn": {
            "id": str(grn.id),
            "grn_number": grn.grn_number,
            "item_code": grn.item_code,
            "batch_no": grn.batch_no,
            "supplier_name": grn.supplier_name,
            "manufacturer_name": grn.manufacturer_name,
            "total_recv_qty": str(grn.total_recv_qty),
            "balance_qty": str(grn.balance_qty),
            "container_qty": str(grn.container_qty),
            "containers_count": grn.containers_count,
            "unit_of_measure": grn.unit_of_measure,
            "recv_date": str(grn.recv_date),
            "mfg_date": str(grn.mfg_date),
            "exp_date": str(grn.exp_date),
            "status": grn.status.value if hasattr(grn.status, "value") else grn.status,
            "rack_no": grn.rack_no,
            "grade": grn.grade,
            "retesting_date": str(grn.retesting_date) if grn.retesting_date else None,
            "material_issue_allowed": grn.material_issue_allowed,
        },
        "material": {
            "item_name": material.item_name if material else None,
            "grade": material.grade if material else None,
        },
        "qc_sampling": {
            "ar_number": sampling.ar_number,
            "sample_qty": str(sampling.sample_qty),
            "sample_date": str(sampling.sample_date),
            "notes": sampling.notes,
        } if sampling else None,
        "qc_decision": {
            "decision": decision.decision.value if hasattr(decision.decision, "value") else decision.decision,
            "test_remarks": decision.test_remarks,
            "retesting_date": str(decision.retesting_date) if decision.retesting_date else None,
            "rejection_reason": decision.rejection_reason,
            "decided_at": str(decision.decided_at),
        } if decision else None,
        "dispensing_summary": {
            "total_dispensed": str(dispensed_row[0]),
            "dispense_count": dispensed_row[1],
        },
    }
