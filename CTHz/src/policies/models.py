from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, CheckConstraint, ForeignKey
from src.database.connection import Base


class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    description = Column(Text)
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_system_policy = Column(Boolean, default=False)
    applies_to = Column(String(16), default="all")
    target_id = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint("applies_to in ('group','station','device','all')", name="ck_policies_applies_to"),
    ) 