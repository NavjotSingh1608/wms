import enum
import uuid

from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Text, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransferStatus(str, enum.Enum):
    PENDING = "PENDING"
    BLOCKED_PENDING_QC_RELEASE = "BLOCKED_PENDING_QC_RELEASE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GradeTransfer(Base):
    __tablename__ = "grade_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=False)
    from_item_code = Column(String(50), ForeignKey("materials.item_code"), nullable=False)
    to_item_code = Column(String(50), ForeignKey("materials.item_code"), nullable=False)
    ar_number_ref = Column(String(50), nullable=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_remarks = Column(Text, nullable=True)
    status = Column(
        SAEnum(TransferStatus, name="transfer_status", create_constraint=True, native_enum=True),
        nullable=False,
        default=TransferStatus.PENDING,
        server_default="PENDING",
    )
    new_grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=True)

    grn = relationship("GRN", foreign_keys=[grn_id])
    from_material = relationship("Material", foreign_keys=[from_item_code], primaryjoin="GradeTransfer.from_item_code == Material.item_code")
    to_material = relationship("Material", foreign_keys=[to_item_code], primaryjoin="GradeTransfer.to_item_code == Material.item_code")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    new_grn = relationship("GRN", foreign_keys=[new_grn_id])
