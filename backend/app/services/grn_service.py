import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRN, GRNStatus
from app.models.stock_ledger import StockLedger, LedgerTxnType, LedgerStage
from app.schemas.grn import GRNCreate, GRNRevise
from app.services.audit_service import log_audit


async def _next_grn_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"GRN-{year}-"
    result = await db.execute(
        select(func.max(GRN.grn_number)).where(GRN.grn_number.like(f"{prefix}%"))
    )
    max_num = result.scalar()
    seq = int(max_num.split("-")[-1]) + 1 if max_num else 1
    return f"{prefix}{seq:04d}"


async def create_grn(db: AsyncSession, payload: GRNCreate, user_id: UUID) -> GRN:
    grn_number = await _next_grn_number(db)
    grn = GRN(
        grn_number=grn_number,
        item_code=payload.item_code,
        batch_no=payload.batch_no,
        supplier_name=payload.supplier_name,
        manufacturer_name=payload.manufacturer_name,
        total_recv_qty=payload.total_recv_qty,
        container_qty=payload.container_qty,
        containers_count=payload.containers_count,
        pack_size_description=payload.pack_size_description,
        unit_of_measure=payload.unit_of_measure,
        recv_date=payload.recv_date,
        mfg_date=payload.mfg_date,
        exp_date=payload.exp_date,
        remarks=payload.remarks,
        grade=payload.grade,
        status=GRNStatus.QUARANTINE,
        balance_qty=payload.total_recv_qty,
        created_by=user_id,
    )
    db.add(grn)
    await db.flush()

    db.add(StockLedger(
        item_code=grn.item_code,
        batch_no=grn.batch_no,
        grn_id=grn.id,
        stage=LedgerStage.QUARANTINE,
        txn_type=LedgerTxnType.IN,
        qty_change=grn.total_recv_qty,
        balance_after=grn.balance_qty,
        ref_type="grn",
        ref_id=grn.id,
        performed_by=user_id,
    ))
    await db.flush()
    return grn


async def get_grn(db: AsyncSession, grn_id: UUID) -> GRN:
    result = await db.execute(
        select(GRN).where(GRN.id == grn_id, GRN.is_active == True)
    )
    grn = result.scalar_one_or_none()
    if not grn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GRN not found")
    return grn


async def list_grns(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 50,
    status_filter: str | None = None,
) -> dict:
    base_filter = [GRN.is_active == True, GRN.deleted_at == None]
    if status_filter:
        base_filter.append(GRN.status == status_filter)

    count_q = select(func.count()).select_from(GRN).where(*base_filter)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(GRN)
        .where(*base_filter)
        .order_by(GRN.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = list((await db.execute(query)).scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 0,
    }


async def revise_grn(
    db: AsyncSession, grn_id: UUID, payload: GRNRevise, user_id: UUID,
) -> GRN:
    original = await get_grn(db, grn_id)
    old_snapshot = {
        "grn_number": original.grn_number,
        "item_code": original.item_code,
        "batch_no": original.batch_no,
        "supplier_name": original.supplier_name,
    }

    new_grn_number = await _next_grn_number(db)
    new_grn = GRN(
        grn_number=new_grn_number,
        item_code=original.item_code,
        batch_no=original.batch_no,
        supplier_name=original.supplier_name,
        manufacturer_name=original.manufacturer_name,
        total_recv_qty=original.total_recv_qty,
        container_qty=original.container_qty,
        containers_count=original.containers_count,
        pack_size_description=original.pack_size_description,
        unit_of_measure=original.unit_of_measure,
        recv_date=original.recv_date,
        mfg_date=original.mfg_date,
        exp_date=original.exp_date,
        remarks=original.remarks,
        grade=original.grade,
        status=original.status,
        balance_qty=original.balance_qty,
        rack_no=original.rack_no,
        material_issue_allowed=original.material_issue_allowed,
        retesting_date=original.retesting_date,
        revised_from_grn_id=original.id,
        created_by=user_id,
    )

    allowed_fields = {
        "item_code", "batch_no", "supplier_name", "manufacturer_name",
        "total_recv_qty", "container_qty", "containers_count",
        "pack_size_description", "unit_of_measure", "recv_date", "mfg_date",
        "exp_date", "remarks", "grade",
    }
    for field, value in payload.revised_fields.items():
        if field in allowed_fields:
            setattr(new_grn, field, value)

    if "total_recv_qty" in payload.revised_fields:
        new_grn.balance_qty = new_grn.total_recv_qty

    db.add(new_grn)

    original.is_active = False
    original.deleted_at = datetime.now(timezone.utc)
    original.updated_by = user_id

    await db.flush()

    await log_audit(
        db, "grn", new_grn.id, "REVISED",
        old_values=old_snapshot,
        new_values={"revised_fields": payload.revised_fields, "reason": payload.revision_reason},
        performed_by=user_id,
    )
    return new_grn


async def update_rack(
    db: AsyncSession, grn_id: UUID, rack_no: str, user_id: UUID,
) -> GRN:
    grn = await get_grn(db, grn_id)
    if grn.status != GRNStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rack can only be assigned to APPROVED GRNs",
        )
    old_rack = grn.rack_no
    grn.rack_no = rack_no
    grn.updated_by = user_id
    grn.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await log_audit(
        db, "grn", grn.id, "RACK_UPDATED",
        old_values={"rack_no": old_rack},
        new_values={"rack_no": rack_no},
        performed_by=user_id,
    )
    return grn
