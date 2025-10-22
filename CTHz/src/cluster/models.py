from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint, Index

from src.database.connection import Base


class DeviceMetadata(Base):
    __tablename__ = "device_metadata"

    key = Column(String(64), primary_key=True)
    value = Column(String(512), nullable=True)


class PairedDevice(Base):
    __tablename__ = "paired_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=False)
    role = Column(String(16), nullable=False)  # manager | sensor
    cluster_id = Column(String(64), nullable=True)
    shared_secret = Column(String(256), nullable=True)  # transitional; will move to mTLS
    paired_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_paired_devices_device_id", "device_id"),
    )


class PairingToken(Base):
    __tablename__ = "pairing_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(256), nullable=False, unique=True)  # jti or full token hash
    source_device_id = Column(String(64), nullable=True)
    target_device_id = Column(String(64), nullable=True)
    cluster_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("token", name="uq_pairing_tokens_token"),
        Index("idx_pairing_tokens_expires_at", "expires_at"),
    )


