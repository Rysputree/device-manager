from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.auth.deps import get_current_user
from src.database.connection import SessionLocal
from src.monitoring.audit import AuditLog


router = APIRouter()


class AuditLogOut(BaseModel):
    id: int
    user: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str
    session_id: Optional[str]

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogOut]


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    request: Request,
    q: Optional[str] = None,
    user: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user),
):
    """List audit logs with optional filters and pagination."""
    if limit > 200:
        limit = 200
    with SessionLocal() as db:
        query = db.query(AuditLog)
        if user:
            query = query.filter(AuditLog.user == user)
        if action:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))
        if q:
            like = f"%{q}%"
            query = query.filter(
                (AuditLog.action.ilike(like)) | (AuditLog.user.ilike(like)) | (AuditLog.user_agent.ilike(like))
            )
        total = query.count()
        rows = query.order_by(desc(AuditLog.id)).offset(offset).limit(limit).all()
        items = []
        for r in rows:
            items.append(AuditLogOut(
                id=r.id,
                user=r.user,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                details=r.details,
                ip_address=r.ip_address,
                user_agent=r.user_agent,
                timestamp=r.timestamp.isoformat() if r.timestamp else "",
                session_id=r.session_id,
            ))
        return AuditLogListResponse(total=total, items=items)


