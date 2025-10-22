from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from src.database.connection import Base


class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    name = Column(String(64), nullable=False)
    location = Column(String(128))
    device_count = Column(Integer, default=0)
    max_devices = Column(Integer, default=3)
    coverage_angle = Column(Integer, default=360)
    manager_device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    status = Column(String(16), default="inactive")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow) 