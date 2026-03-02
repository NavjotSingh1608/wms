import enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Text, Index, Enum as SAEnum, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationType(str, enum.Enum):
    RETEST_ALERT = "RETEST_ALERT"
    EXPIRY_ALERT = "EXPIRY_ALERT"
    LABEL_REPRINT_REQUEST = "LABEL_REPRINT_REQUEST"
    GRADE_TRANSFER_REQUEST = "GRADE_TRANSFER_REQUEST"
    FG_PENDING_QA = "FG_PENDING_QA"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(
        SAEnum(NotificationType, name="notification_type", create_constraint=True, native_enum=True),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    ref_type = Column(String(50), nullable=True)
    ref_id = Column(UUID(as_uuid=True), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    user = relationship("User", foreign_keys=[user_id])
