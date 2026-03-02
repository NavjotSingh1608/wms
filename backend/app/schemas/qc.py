from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SamplingCreate(BaseModel):
    grn_id: UUID
    ar_number: str = Field(..., pattern=r"^AR-\d{4}-\d{4}$")
    sample_qty: Decimal
    notes: str | None = None


class SamplingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_id: UUID
    ar_number: str
    sample_qty: Decimal
    sampled_by: UUID
    notes: str | None = None


class DecisionCreate(BaseModel):
    grn_id: UUID
    decision: str = Field(..., pattern=r"^(APPROVED|REJECTED)$")
    test_remarks: str | None = None
    retesting_date: date | None = None
    rejection_reason: str | None = None

    @model_validator(mode="after")
    def _validate_decision(self):
        if self.decision == "APPROVED":
            if not self.retesting_date:
                raise ValueError("retesting_date is required for APPROVED decisions")
            if self.retesting_date <= date.today():
                raise ValueError("retesting_date must be in the future")
        if self.decision == "REJECTED" and not self.rejection_reason:
            raise ValueError("rejection_reason is required for REJECTED decisions")
        return self


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grn_id: UUID
    sampling_id: UUID
    decision: str
    test_remarks: str | None = None
    rejection_reason: str | None = None
    retesting_date: date | None = None
    decided_by: UUID
    retest_cycle_no: int
