import enum
import uuid

from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Numeric, Index, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LedgerTxnType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"


class LedgerStage(str, enum.Enum):
    QUARANTINE = "QUARANTINE"
    UNDER_TEST = "UNDER_TEST"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    QUARANTINE_RETESTING = "QUARANTINE_RETESTING"
    FINISHED_GOODS = "FINISHED_GOODS"
    DISPATCHED = "DISPATCHED"


class StockLedger(Base):
    __tablename__ = "stock_ledger"
    __table_args__ = (
        Index("ix_stock_ledger_item_batch", "item_code", "batch_no"),
        Index("ix_stock_ledger_grn_id", "grn_id"),
        Index("ix_stock_ledger_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    item_code = Column(String(50), ForeignKey("materials.item_code"), nullable=False)
    batch_no = Column(String(100), nullable=False)
    grn_id = Column(UUID(as_uuid=True), ForeignKey("grn.id"), nullable=True)
    fg_id = Column(UUID(as_uuid=True), ForeignKey("finished_goods.id"), nullable=True)
    stage = Column(
        SAEnum(LedgerStage, name="ledger_stage", create_constraint=True, native_enum=True),
        nullable=False,
    )
    txn_type = Column(
        SAEnum(LedgerTxnType, name="ledger_txn_type", create_constraint=True, native_enum=True),
        nullable=False,
    )
    qty_change = Column(Numeric(15, 4), nullable=False)
    balance_after = Column(Numeric(15, 4), nullable=False)
    ref_type = Column(String(50), nullable=True)
    ref_id = Column(UUID(as_uuid=True), nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    material = relationship("Material", foreign_keys=[item_code], primaryjoin="StockLedger.item_code == Material.item_code")
    grn = relationship("GRN", foreign_keys=[grn_id])
    finished_good = relationship("FinishedGoods", foreign_keys=[fg_id])
    performer = relationship("User", foreign_keys=[performed_by])
