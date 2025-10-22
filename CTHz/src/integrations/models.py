from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from src.database.connection import Base


class Integration(Base):
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    integration_type = Column(String(32), nullable=False)
    name = Column(String(64), nullable=False)
    config = Column(JSON, nullable=False)
    credentials_encrypted = Column(Text)
    is_active = Column(Boolean, default=True)
    last_test = Column(DateTime)
    test_result = Column(String(16))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow) 