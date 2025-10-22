from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from src.database.connection import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(16), nullable=False)
    email = Column(String(128))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    __table_args__ = (
        CheckConstraint("role in ('owner','admin','monitor')", name="ck_users_role"),
    ) 