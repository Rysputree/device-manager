from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from src.database.connection import Base


class ArchiveServer(Base):
    __tablename__ = "archive_servers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    server_url = Column(String(256), nullable=False)
    auth_type = Column(String(16), default="token")
    credentials_encrypted = Column(Text)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow) 