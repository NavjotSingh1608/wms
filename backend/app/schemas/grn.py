from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class GRNCreate(BaseModel):
    item_code: str
    batch_no: str
    supplier_name: str
    manufacturer_name: str
    total_recv_qty: Decimal
    container_qty: Decimal
    containers_count: int
    pack_size_description: str | None = None
    unit_of_measure: str
    recv_date: date
    mfg_date: date
    exp_date: date
    remarks: str | None = None
    grade: str | None = None

    @model_validator(mode="after")
    def _cross_field(self):
        if self.exp_date <= self.mfg_date:
            raise ValueError("exp_date must be after mfg_date")
        if self.grade == "IP" and not self.remarks:
            raise ValueError("remarks is required when grade is IP")
        return self


class GRNOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_number: str
    item_code: str
    batch_no: str
    supplier_name: str
    manufacturer_name: str
    total_recv_qty: Decimal
    container_qty: Decimal
    containers_count: int
    pack_size_description: str | None = None
    unit_of_measure: str
    recv_date: date
    mfg_date: date
    exp_date: date
    status: str
    material_issue_allowed: bool
    rack_no: str | None = None
    remarks: str | None = None
    grade: str | None = None
    balance_qty: Decimal
    retesting_date: date | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class GRNListOut(BaseModel):
    items: list[GRNOut]
    total: int
    page: int
    per_page: int
    pages: int


class GRNRevise(BaseModel):
    revised_fields: dict
    revision_reason: str


class RackUpdate(BaseModel):
    rack_no: str
