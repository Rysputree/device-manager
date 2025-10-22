from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.database.connection import SessionLocal
from src.auth.models import User


class SetupLockMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Allow setup endpoints and health regardless
        if path.startswith("/api/auth/setup") or path.startswith("/api/setup") or path.startswith("/healthz") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi") or path.startswith("/setup") or path.startswith("/"):
            return await call_next(request)
        with SessionLocal() as db:
            has_user = db.query(User).count() > 0
        if not has_user:
            return JSONResponse(status_code=423, content={"code": "locked", "message": "System not configured. Complete setup."})
        return await call_next(request) 