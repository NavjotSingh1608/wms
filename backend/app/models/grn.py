import enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, Integer, ForeignKey, DateTime, Date,
    Numeric, Text, Index, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class GRNStatus(str, enum.Enum):
    QUARANTINE = "QUARANTINE"
    UNDER_TEST = "UNDER_TEST"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    QUARANTINE_RETESTING = "QUARANTINE_RETESTING"
    BLOCKED_PENDING_QC_RELEASE = "BLOCKED_PENDING_QC_RELEASE"
    FULLY_DISPENSED = "FULLY_DISPENSED"
    APPROVED_BP_USP = "APPROVED_BP_USP"


class GRN(Base):
    __tablename__ = "grn"
    __table_args__ = (
        Index("ix_grn_item_code", "item_code"),
        Index("ix_grn_status", "status"),
        Index("ix_grn_exp_date", "exp_date"),
        Index("ix_grn_batch_no", "batch_no"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_number = Column(String(20), unique=True, nullable=False)
    item_code = Column(String(50), ForeignKey("materials.item_code"), nullable=False)
    batch_no = Column(String(100), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    manufacturer_name = Column(String(255), nullable=False)
    total_recv_qty = Column(Numeric(15, 4), nullable=False)
    container_qty = Column(Numeric(15, 4), nullable=False)
    containers_count = Column(Integer, nullable=False)
    pack_size_description = Column(String(100), nullable=True)
    unit_of_measure = Column(String(20), nullable=False)
    recv_date = Column(Date, nullable=False)
    mfg_date = Column(Date, nullable=False)
    exp_date = Column(Date, nullable=False)
    status = Column(
        SAEnum(GRNStatus, name="grn_status", create_constraint=True, native_enum=True),
        nullable=False,
        default=GRNStatus.QUARANTINE,
        server_default="QUARANTINE",
    )
    material_issue_allowed = Column(Boolean, nullable=False, default=False, server_default="false")
    rack_no = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    grade = Column(String(20), nullable=True)
    revised_from_grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    balance_qty = Column(Numeric(15, 4), nullable=False)
    retest_alert_sent = Column(Boolean, nullable=False, default=False, server_default="false")
    retest_alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    retesting_date = Column(Date, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    material = relationship("Material", foreign_keys=[item_code], primaryjoin="GRN.item_code == Material.item_code")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    revised_from = relationship("GRN", remote_side="GRN.id", foreign_keys=[revised_from_grn_id])
