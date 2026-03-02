import enum
import uuid

from sqlalchemy import (
    Column, Integer, ForeignKey, DateTime, Boolean, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RetestOutcome(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RetestingCycle(Base):
    __tablename__ = "retesting_cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=False)
    cycle_no = Column(Integer, nullable=False)
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    initiated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    new_label_id = Column(UUID(as_uuid=True), ForeignKey("qr_labels.id"), nullable=True)
    retest_alert_sent = Column(Boolean, nullable=False, default=False, server_default="false")
    retest_alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(
        SAEnum(RetestOutcome, name="retest_outcome", create_constraint=True, native_enum=True),
        nullable=True,
    )

    grn = relationship("GRN", foreign_keys=[grn_id])
    initiator = relationship("User", foreign_keys=[initiated_by])
    new_label = relationship("QRLabel", foreign_keys=[new_label_id])
