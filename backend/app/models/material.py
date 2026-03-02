import uuid

from sqlalchemy import Column, String, Boolean, Text, DateTime, text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    item_code = Column(String(50), unique=True, nullable=False)
    item_name = Column(String(255), nullable=False)
    grade = Column(String(20), nullable=True)
    unit_of_measure = Column(String(20), nullable=False)
    specifications = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
