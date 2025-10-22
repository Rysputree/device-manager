from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from src.database.connection import Base


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    description = Column(Text)
    location = Column(String(128))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow) 