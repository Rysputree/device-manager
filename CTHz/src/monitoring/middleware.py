from __future__ import annotations
from typing import Callable
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from datetime import datetime, timezone

from src.monitoring.audit import AuditEvent, log_audit


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start = datetime.now(timezone.utc)
        response: Response = None
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Create a basic error response if none exists
            if response is None:
                from starlette.responses import JSONResponse
                response = JSONResponse(status_code=500, content={"error": "Internal server error"})
            raise e
        finally:
            if response is not None:
                duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000.0
                # Extract minimal user/context; hook into auth later
                user = getattr(request.state, "user", None)
                session_id = request.cookies.get("session_id")
                ev = AuditEvent(
                    action=f"{request.method} {request.url.path}",
                    user=getattr(user, "username", None) if user else None,
                    resource_type="http",
                    resource_id=str(response.status_code),
                    details={
                        "query": dict(request.query_params),
                        "status": response.status_code,
                        "duration_ms": round(duration_ms, 2),
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    session_id=session_id,
                )
                log_audit(ev)
