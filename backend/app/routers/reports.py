from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.user import User
from app.schemas.reports import StockReportFilters, StockReportOut
from app.services import stock_service

router = APIRouter()


@router.get("/reports/stock", response_model=StockReportOut)
async def stock_report(
    item_name: str | None = Query(None),
    item_code: str | None = Query(None),
    batch_no: str | None = Query(None),
    ar_number: str | None = Query(None),
    status: list[str] | None = Query(None),
    recv_date_from: date | None = Query(None),
    recv_date_to: date | None = Query(None),
    exp_date_from: date | None = Query(None),
    exp_date_to: date | None = Query(None),
    is_retest: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:view")),
):
    filters = StockReportFilters(
        item_name=item_name,
        item_code=item_code,
        batch_no=batch_no,
        ar_number=ar_number,
        status=status,
        recv_date_from=recv_date_from,
        recv_date_to=recv_date_to,
        exp_date_from=exp_date_from,
        exp_date_to=exp_date_to,
        is_retest=is_retest,
        page=page,
        per_page=per_page,
    )
    return await stock_service.get_stock_report(db, filters)


@router.get("/reports/stock/export")
async def export_stock_report(
    item_name: str | None = Query(None),
    item_code: str | None = Query(None),
    batch_no: str | None = Query(None),
    ar_number: str | None = Query(None),
    status: list[str] | None = Query(None),
    recv_date_from: date | None = Query(None),
    recv_date_to: date | None = Query(None),
    exp_date_from: date | None = Query(None),
    exp_date_to: date | None = Query(None),
    is_retest: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:view")),
):
    filters = StockReportFilters(
        item_name=item_name,
        item_code=item_code,
        batch_no=batch_no,
        ar_number=ar_number,
        status=status,
        recv_date_from=recv_date_from,
        recv_date_to=recv_date_to,
        exp_date_from=exp_date_from,
        exp_date_to=exp_date_to,
        is_retest=is_retest,
    )
    csv_bytes = await stock_service.export_csv(db, filters)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock_report.csv"},
    )
