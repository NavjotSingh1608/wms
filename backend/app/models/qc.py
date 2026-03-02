import enum
import uuid

from sqlalchemy import (
    Column, String, Integer, ForeignKey, DateTime, Date,
    Numeric, Text, Enum as SAEnum, CheckConstraint, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class QCDecisionType(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class QCSampling(Base):
    __tablename__ = "qc_sampling"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=False)
    ar_number = Column(String(50), unique=True, nullable=False)
    sample_qty = Column(Numeric(15, 4), nullable=False)
    sampled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sample_date = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    grn = relationship("GRN", foreign_keys=[grn_id])
    sampler = relationship("User", foreign_keys=[sampled_by])


class QCDecision(Base):
    __tablename__ = "qc_decisions"
    __table_args__ = (
        CheckConstraint(
            "(decision != 'REJECTED' OR rejection_reason IS NOT NULL)",
            name="ck_qc_decisions_rejected_reason",
        ),
        CheckConstraint(
            "(decision != 'APPROVED' OR retesting_date IS NOT NULL)",
            name="ck_qc_decisions_approved_retest",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=False)
    sampling_id = Column(UUID(as_uuid=True), ForeignKey("qc_sampling.id"), nullable=False)
    decision = Column(
        SAEnum(QCDecisionType, name="qc_decision_type", create_constraint=True, native_enum=True),
        nullable=False,
    )
    test_remarks = Column(Text, nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    retesting_date = Column(Date, nullable=True)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    retest_cycle_no = Column(Integer, nullable=False, default=0, server_default="0")

    grn = relationship("GRN", foreign_keys=[grn_id])
    sampling = relationship("QCSampling", foreign_keys=[sampling_id])
    decider = relationship("User", foreign_keys=[decided_by])
