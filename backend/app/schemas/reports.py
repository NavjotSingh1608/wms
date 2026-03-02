from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StockReportFilters(BaseModel):
    item_name: str | None = None
    item_code: str | None = None
    batch_no: str | None = None
    ar_number: str | None = None
    status: list[str] | None = None
    recv_date_from: date | None = None
    recv_date_to: date | None = None
    exp_date_from: date | None = None
    exp_date_to: date | None = None
    is_retest: bool | None = None
    page: int = 1
    per_page: int = 50


class StockReportRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grn_id: UUID
    grn_number: str
    item_code: str
    item_name: str
    batch_no: str
    supplier_name: str
    manufacturer_name: str
    grade: str | None = None
    recv_date: date
    mfg_date: date
    exp_date: date
    status: str
    ar_number: str | None = None
    rack_no: str | None = None
    total_recv_qty: Decimal
    balance_qty: Decimal
    qty_quarantine: Decimal = Decimal("0")
    qty_under_test: Decimal = Decimal("0")
    qty_approved: Decimal = Decimal("0")
    qty_rejected: Decimal = Decimal("0")
    qty_dispensed: Decimal = Decimal("0")
    retesting_date: date | None = None
    material_issue_allowed: bool


class StockReportOut(BaseModel):
    items: list[StockReportRow]
    total: int
    page: int
    per_page: int
    pages: int
