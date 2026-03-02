from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DispenseRequest(BaseModel):
    grn_id: UUID | None = None
    item_code: str
    product_name: str
    product_batch_no: str
    qty_to_issue: Decimal


class DispenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dispense_id: UUID
    qty_issued: Decimal
    balance_qty_after: Decimal
    issued_by: UUID
    issued_at: datetime


class QueueBatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grn_id: UUID
    grn_number: str
    batch_no: str
    available_qty: Decimal
    exp_date: date
    recv_date: date


class DispenseQueueOut(BaseModel):
    item_code: str
    item_name: str
    total_available_qty: Decimal
    batches: list[QueueBatch]
