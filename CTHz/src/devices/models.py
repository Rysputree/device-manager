from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint, JSON
from src.database.connection import Base


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(32), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    model = Column(String(32), nullable=False, default="CTHz-300")
    serial_number = Column(String(64), unique=True)
    firmware_version = Column(String(16))
    hardware_version = Column(String(16))
    ip_address = Column(String(64))
    mac_address = Column(String(17))
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    device_role = Column(String(16), default="sensor")
    location = Column(String(128))
    timezone = Column(String(32), default="UTC")
    status = Column(String(16), default="offline")
    last_seen = Column(DateTime)
    last_calibrated = Column(DateTime)
    discovery_enabled = Column(Boolean, default=False)
    ssid_broadcast = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint("device_role in ('manager','sensor')", name="ck_devices_role"),
    )


class DeviceConfiguration(Base):
    __tablename__ = "device_configurations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    configuration = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    applied_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow) 