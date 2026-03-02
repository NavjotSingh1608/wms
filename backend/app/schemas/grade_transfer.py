from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransferRequest(BaseModel):
    grn_id: UUID
    from_item_code: str
    to_item_code: str
    ar_number: str | None = None
    remarks: str


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transfer_id: UUID
    grn_id: UUID
    from_item_code: str
    to_item_code: str
    status: str
    requested_by: UUID
    requested_at: datetime
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    new_grn_id: UUID | None = None
