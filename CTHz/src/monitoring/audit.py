from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict, Optional
import logging
import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.orm import Session

from src.database.connection import Base, SessionLocal
from src.config.settings import Settings

settings = Settings()


class AuditSinkMode(str, Enum):
    db = "db"
    file = "file"
    both = "both"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(128))
    action = Column(String(128), nullable=False)
    resource_type = Column(String(64))
    resource_id = Column(String(64))
    details = Column(JSON)
    ip_address = Column(String(64))
    user_agent = Column(String(256))
    timestamp = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    session_id = Column(String(128))


@dataclass
class AuditEvent:
    action: str
    user: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


class AuditSink:
    def __init__(self) -> None:
        self.mode = AuditSinkMode(settings.audit_sink_mode) if hasattr(settings, "audit_sink_mode") else AuditSinkMode.db
        self._logger = logging.getLogger("audit")
        self._file_handler: Optional[TimedRotatingFileHandler] = None
        if self.mode in (AuditSinkMode.file, AuditSinkMode.both):
            log_path = getattr(settings, "audit_log_file", "./logs/audit.log")
            self._file_handler = TimedRotatingFileHandler(log_path, when="midnight", backupCount=getattr(settings, "audit_backup_count", 7))
            formatter = logging.Formatter('%(message)s')
            self._file_handler.setFormatter(formatter)
            self._logger.setLevel(logging.INFO)
            self._logger.addHandler(self._file_handler)

    def write(self, event: AuditEvent) -> None:
        utc_now = datetime.now(timezone.utc).isoformat()
        payload = {
            "ts": utc_now,
            "action": event.action,
            "user": event.user,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "details": event.details,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "session_id": event.session_id,
        }
        if self.mode in (AuditSinkMode.db, AuditSinkMode.both):
            with SessionLocal() as db:
                self._write_db(db, payload)
        if self.mode in (AuditSinkMode.file, AuditSinkMode.both):
            self._write_file(payload)

    def _write_db(self, db: Session, payload: Dict[str, Any]) -> None:
        row = AuditLog(
            user=payload.get("user"),
            action=payload["action"],
            resource_type=payload.get("resource_type"),
            resource_id=payload.get("resource_id"),
            details=payload.get("details"),
            ip_address=payload.get("ip_address"),
            user_agent=payload.get("user_agent"),
            session_id=payload.get("session_id"),
        )
        db.add(row)
        db.commit()

    def _write_file(self, payload: Dict[str, Any]) -> None:
        # log as a single-line JSON record
        self._logger.info(json.dumps(payload, separators=(",", ":")))


audit_sink = AuditSink()

def log_audit(event: AuditEvent) -> None:
    audit_sink.write(event) 