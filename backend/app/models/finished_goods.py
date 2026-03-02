import enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Date,
    Numeric, Text, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class FGStatus(str, enum.Enum):
    PENDING_QA_VERIFICATION = "PENDING_QA_VERIFICATION"
    QA_VERIFIED = "QA_VERIFIED"
    QA_APPROVED = "QA_APPROVED"
    QA_REJECTED = "QA_REJECTED"
    WH_RECEIVED = "WH_RECEIVED"
    DISPATCHED = "DISPATCHED"


class FinishedGoods(Base):
    __tablename__ = "finished_goods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    product_name = Column(String(255), nullable=False)
    product_code = Column(String(50), nullable=True)
    batch_no = Column(String(100), nullable=False)
    mfg_date = Column(Date, nullable=False)
    exp_date = Column(Date, nullable=False)
    total_qty = Column(Numeric(15, 4), nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    status = Column(
        SAEnum(FGStatus, name="fg_status", create_constraint=True, native_enum=True),
        nullable=False,
        default=FGStatus.PENDING_QA_VERIFICATION,
        server_default="PENDING_QA_VERIFICATION",
    )
    sent_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    qa_verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    qa_verified_at = Column(DateTime(timezone=True), nullable=True)
    qa_approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    qa_approved_at = Column(DateTime(timezone=True), nullable=True)
    qa_rejection_reason = Column(Text, nullable=True)
    wh_received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    wh_received_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(Text, nullable=True)
    revised_from_fg_id = Column(UUID(as_uuid=True), ForeignKey("finished_goods.id"), nullable=True)
    revised_by = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    sender = relationship("User", foreign_keys=[sent_by])
    qa_verifier = relationship("User", foreign_keys=[qa_verified_by])
    qa_approver = relationship("User", foreign_keys=[qa_approved_by])
    wh_receiver = relationship("User", foreign_keys=[wh_received_by])
    dispatcher = relationship("User", foreign_keys=[dispatched_by])
    revised_from = relationship("FinishedGoods", remote_side="FinishedGoods.id", foreign_keys=[revised_from_fg_id])


class ShipperLabel(Base):
    __tablename__ = "shipper_labels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    fg_id = Column(UUID(as_uuid=True), ForeignKey("finished_goods.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    batch_no = Column(String(100), nullable=False)
    mfg_date = Column(Date, nullable=False)
    exp_date = Column(Date, nullable=False)
    net_weight = Column(Numeric(10, 4), nullable=True)
    gross_weight = Column(Numeric(10, 4), nullable=True)
    quantity = Column(Numeric(15, 4), nullable=True)
    carton_no = Column(String(50), nullable=True)
    barcode_data = Column(Text, nullable=False)
    s3_key = Column(String(500), nullable=True)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    finished_good = relationship("FinishedGoods", foreign_keys=[fg_id])
    generator = relationship("User", foreign_keys=[generated_by])
