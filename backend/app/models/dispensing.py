import uuid

from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Numeric, Text, Index, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Dispensing(Base):
    __tablename__ = "dispensing"
    __table_args__ = (
        Index("ix_dispensing_grn_id", "grn_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_batch_no = Column(String(100), nullable=False)
    qty_issued = Column(Numeric(15, 4), nullable=False)
    issued_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    balance_qty_after = Column(Numeric(15, 4), nullable=False)
    notes = Column(Text, nullable=True)

    grn = relationship("GRN", foreign_keys=[grn_id])
    issuer = relationship("User", foreign_keys=[issued_by])
