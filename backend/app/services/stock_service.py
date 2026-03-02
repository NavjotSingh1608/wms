import csv
import io
import math
from decimal import Decimal

from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grn import GRN
from app.models.material import Material
from app.models.qc import QCSampling
from app.models.stock_ledger import StockLedger, LedgerStage
from app.schemas.reports import StockReportFilters


def _stage_subquery(stage: LedgerStage):
    return (
        select(func.coalesce(func.sum(StockLedger.qty_change), 0))
        .where(StockLedger.grn_id == GRN.id, StockLedger.stage == stage)
        .correlate(GRN)
        .scalar_subquery()
    )


def _latest_ar_subquery():
    return (
        select(QCSampling.ar_number)
        .where(QCSampling.grn_id == GRN.id)
        .order_by(QCSampling.created_at.desc())
        .limit(1)
        .correlate(GRN)
        .scalar_subquery()
    )


async def get_stock_report(db: AsyncSession, filters: StockReportFilters) -> dict:
    latest_ar = _latest_ar_subquery()

    query = (
        select(
            GRN.id.label("grn_id"),
            GRN.grn_number,
            GRN.item_code,
            Material.item_name,
            GRN.batch_no,
            GRN.supplier_name,
            GRN.manufacturer_name,
            GRN.grade,
            GRN.recv_date,
            GRN.mfg_date,
            GRN.exp_date,
            GRN.status,
            latest_ar.label("ar_number"),
            GRN.rack_no,
            GRN.total_recv_qty,
            GRN.balance_qty,
            _stage_subquery(LedgerStage.QUARANTINE).label("qty_quarantine"),
            _stage_subquery(LedgerStage.UNDER_TEST).label("qty_under_test"),
            _stage_subquery(LedgerStage.APPROVED).label("qty_approved"),
            _stage_subquery(LedgerStage.REJECTED).label("qty_rejected"),
            (GRN.total_recv_qty - GRN.balance_qty).label("qty_dispensed"),
            GRN.retesting_date,
            GRN.material_issue_allowed,
        )
        .join(Material, Material.item_code == GRN.item_code)
        .where(GRN.is_active == True, GRN.deleted_at == None)
    )

    if filters.item_name:
        query = query.where(Material.item_name.ilike(f"%{filters.item_name}%"))
    if filters.item_code:
        query = query.where(GRN.item_code == filters.item_code)
    if filters.batch_no:
        query = query.where(GRN.batch_no.ilike(f"%{filters.batch_no}%"))
    if filters.ar_number:
        query = query.where(latest_ar == filters.ar_number)
    if filters.status:
        query = query.where(GRN.status.in_(filters.status))
    if filters.recv_date_from:
        query = query.where(GRN.recv_date >= filters.recv_date_from)
    if filters.recv_date_to:
        query = query.where(GRN.recv_date <= filters.recv_date_to)
    if filters.exp_date_from:
        query = query.where(GRN.exp_date >= filters.exp_date_from)
    if filters.exp_date_to:
        query = query.where(GRN.exp_date <= filters.exp_date_to)
    if filters.is_retest is True:
        query = query.where(GRN.retesting_date != None)
    elif filters.is_retest is False:
        query = query.where(GRN.retesting_date == None)

    count_sub = query.subquery()
    total = (await db.execute(select(func.count()).select_from(count_sub))).scalar() or 0

    query = query.order_by(GRN.created_at.desc()).offset(
        (filters.page - 1) * filters.per_page
    ).limit(filters.per_page)

    rows = (await db.execute(query)).mappings().all()

    items = [
        {
            "grn_id": r["grn_id"],
            "grn_number": r["grn_number"],
            "item_code": r["item_code"],
            "item_name": r["item_name"],
            "batch_no": r["batch_no"],
            "supplier_name": r["supplier_name"],
            "manufacturer_name": r["manufacturer_name"],
            "grade": r["grade"],
            "recv_date": r["recv_date"],
            "mfg_date": r["mfg_date"],
            "exp_date": r["exp_date"],
            "status": r["status"].value if hasattr(r["status"], "value") else r["status"],
            "ar_number": r["ar_number"],
            "rack_no": r["rack_no"],
            "total_recv_qty": r["total_recv_qty"],
            "balance_qty": r["balance_qty"],
            "qty_quarantine": r["qty_quarantine"],
            "qty_under_test": r["qty_under_test"],
            "qty_approved": r["qty_approved"],
            "qty_rejected": r["qty_rejected"],
            "qty_dispensed": r["qty_dispensed"],
            "retesting_date": r["retesting_date"],
            "material_issue_allowed": r["material_issue_allowed"],
        }
        for r in rows
    ]

    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "pages": math.ceil(total / filters.per_page) if filters.per_page else 0,
    }


async def export_csv(db: AsyncSession, filters: StockReportFilters) -> bytes:
    filters.page = 1
    filters.per_page = 100_000
    data = await get_stock_report(db, filters)

    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "GRN Number", "Item Code", "Item Name", "Batch No", "Supplier",
        "Manufacturer", "Grade", "Recv Date", "Mfg Date", "Exp Date",
        "Status", "AR Number", "Rack No", "Total Recv Qty", "Balance Qty",
        "Qty Quarantine", "Qty Under Test", "Qty Approved", "Qty Rejected",
        "Qty Dispensed", "Retesting Date", "Material Issue Allowed",
    ]
    writer.writerow(headers)

    for row in data["items"]:
        writer.writerow([
            row["grn_number"], row["item_code"], row["item_name"],
            row["batch_no"], row["supplier_name"], row["manufacturer_name"],
            row["grade"], row["recv_date"], row["mfg_date"], row["exp_date"],
            row["status"], row["ar_number"], row["rack_no"],
            row["total_recv_qty"], row["balance_qty"],
            row["qty_quarantine"], row["qty_under_test"],
            row["qty_approved"], row["qty_rejected"], row["qty_dispensed"],
            row["retesting_date"], row["material_issue_allowed"],
        ])

    return output.getvalue().encode("utf-8")
