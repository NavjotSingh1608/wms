from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FGCreate(BaseModel):
    product_name: str
    product_code: str | None = None
    batch_no: str
    mfg_date: date
    exp_date: date
    total_qty: Decimal
    unit_of_measure: str
    remarks: str | None = None


class FGOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: str
    product_code: str | None = None
    batch_no: str
    mfg_date: date
    exp_date: date
    total_qty: Decimal
    unit_of_measure: str
    status: str
    sent_by: UUID
    sent_at: datetime
    qa_verified_by: UUID | None = None
    qa_verified_at: datetime | None = None
    qa_approved_by: UUID | None = None
    qa_approved_at: datetime | None = None
    qa_rejection_reason: str | None = None
    wh_received_by: UUID | None = None
    wh_received_at: datetime | None = None
    dispatched_by: UUID | None = None
    dispatched_at: datetime | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class FGListOut(BaseModel):
    items: list[FGOut]
    total: int
    page: int
    per_page: int
    pages: int


class ShipperLabelCreate(BaseModel):
    fg_id: UUID
    net_weight: Decimal
    gross_weight: Decimal
    quantity: Decimal
    carton_no: str
