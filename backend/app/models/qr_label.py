import enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Text, Index, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LabelType(str, enum.Enum):
    QUARANTINE = "QUARANTINE"
    QUARANTINE_RETESTING = "QUARANTINE_RETESTING"
    SHIPPER = "SHIPPER"


class QRLabel(Base):
    __tablename__ = "qr_labels"
    __table_args__ = (
        Index("ix_qr_labels_grn_current", "grn_id", "is_current"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=True)
    fg_id = Column(UUID(as_uuid=True), nullable=True)
    label_type = Column(
        SAEnum(LabelType, name="label_type", create_constraint=True, native_enum=True),
        nullable=False,
    )
    qr_data = Column(Text, nullable=False)
    s3_key = Column(String(500), nullable=True)
    is_current = Column(Boolean, nullable=False, default=True, server_default="true")
    reprint_authorized_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    grn = relationship("GRN", foreign_keys=[grn_id])
    reprint_authorizer = relationship("User", foreign_keys=[reprint_authorized_by])
    generator = relationship("User", foreign_keys=[generated_by])
