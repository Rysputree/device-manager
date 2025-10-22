from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, CheckConstraint, ForeignKey
from src.database.connection import Base


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    source_type = Column(String(16))
    source_id = Column(Integer)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint("severity in ('critical','warning','info')", name="ck_alerts_severity"),
        CheckConstraint("source_type in ('group','station','device','system')", name="ck_alerts_source_type"),
    ) 