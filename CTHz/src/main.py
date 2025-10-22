import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request as StarletteRequest

from src.config.settings import Settings
from src.utils.logging import configure_logging, get_logger
from src.monitoring.middleware import AuditLoggingMiddleware
from src.database.init_db import init_db
from src.middleware.setup_lock import SetupLockMiddleware
from src.database.connection import SessionLocal
from src.auth.models import User
from src.auth.deps import get_current_user, get_current_user_from_cookie
from src.auth.permissions import check_module_access

# Resolve settings and logging
settings = Settings()
configure_logging()
logger = get_logger(__name__)

# Templates
templates = Jinja2Templates(directory="src/templates")

# Disable interactive docs in production
docs_url = None if settings.environment == "production" else "/docs"
redoc_url = None if settings.environment == "production" else "/redoc"

app = FastAPI(
    title="CTHz Device Manager",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize DB (dev convenience)
try:
    init_db()
except Exception as e:
    logger.error("DB init failed: %s", e)

# Setup lock must be early
app.add_middleware(SetupLockMiddleware)

# CORS (tighten as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost", "https://127.0.0.1", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit logging middleware
app.add_middleware(AuditLoggingMiddleware)


@app.middleware("http")
async def add_request_id_and_logging(request: StarletteRequest, call_next):
    response = None
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.exception("Unhandled exception")
        return JSONResponse(status_code=500, content={"code": "internal_error", "message": "Unexpected server error"})


@app.get("/healthz", tags=["system"])  # internal health for container/orchestrator
async def healthz():
    return {"ok": True}


@app.get("/")
async def root(request: Request):
    """Redirect to setup if not initialized, otherwise to login"""
    with SessionLocal() as db:
        has_user = db.query(User).count() > 0
    
    if not has_user:
        return RedirectResponse(url="/setup")
    else:
        return RedirectResponse(url="/login")


@app.get("/setup")
async def setup_page(request: Request):
    """Setup wizard page"""
    return templates.TemplateResponse("setup/wizard.html", {"request": request})


@app.get("/login")
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/dashboard")
async def dashboard(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Main dashboard"""
    return templates.TemplateResponse("dashboard/index.html", {"request": request, "user": current_user})


@app.get("/devices")
async def devices_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Device management page"""
    return templates.TemplateResponse("devices/index.html", {"request": request, "user": current_user})


@app.get("/monitoring")
async def monitoring_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Live monitoring page"""
    return templates.TemplateResponse("monitoring/index.html", {"request": request, "user": current_user})


@app.get("/policies")
async def policies_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Policy management page"""
    return templates.TemplateResponse("policies/index.html", {"request": request, "user": current_user})


@app.get("/alerts")
async def alerts_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Alerts & notifications page"""
    return templates.TemplateResponse("alerts/index.html", {"request": request, "user": current_user})


@app.get("/configuration")
async def configuration_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Configuration page"""
    # Check permissions manually to provide better error handling
    user_role = current_user.get("role")
    if user_role == "monitor":
        # Redirect monitor users to dashboard with error message
        return RedirectResponse(url="/dashboard?error=access_denied&message=You do not have permission to access Configuration", status_code=302)
    
    return templates.TemplateResponse("configuration/index.html", {"request": request, "user": current_user})


@app.get("/storage")
async def storage_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Storage management page"""
    return templates.TemplateResponse("storage/index.html", {"request": request, "user": current_user})


@app.get("/audit")
async def audit_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Audit logs page"""
    # Check permissions manually to provide better error handling
    user_role = current_user.get("role")
    if user_role == "monitor":
        # Redirect monitor users to dashboard with error message
        return RedirectResponse(url="/dashboard?error=access_denied&message=You do not have permission to access Audit Logs", status_code=302)
    
    return templates.TemplateResponse("audit/index.html", {"request": request, "user": current_user})


@app.get("/users")
async def users_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """User management page"""
    # Check permissions manually to provide better error handling
    user_role = current_user.get("role")
    if user_role == "monitor":
        # Redirect monitor users to dashboard with error message
        return RedirectResponse(url="/dashboard?error=access_denied&message=You do not have permission to access User Management", status_code=302)
    
    return templates.TemplateResponse("users/index.html", {"request": request, "user": current_user})


@app.get("/live-video")
async def live_video_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Live Video Feed page"""
    return templates.TemplateResponse("monitoring/index.html", {"request": request, "user": current_user})


@app.get("/errors")
async def errors_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Error handling page"""
    return templates.TemplateResponse("errors/index.html", {"request": request, "user": current_user})


@app.get("/discovery")
async def discovery_page(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    """Discovery & pairing page"""
    # Check permissions manually to provide better error handling
    user_role = current_user.get("role")
    if user_role == "monitor":
        # Redirect monitor users to dashboard with error message
        return RedirectResponse(url="/dashboard?error=access_denied&message=You do not have permission to access Discovery & Pairing", status_code=302)
    
    return templates.TemplateResponse("discovery/index.html", {"request": request, "user": current_user})


# Router includes (placeholders; implement modules gradually)
try:
    from src.auth.routes import router as auth_router  # type: ignore
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
except Exception:
    logger.warning("Auth router not available yet; skipping include")

try:
    from src.setup.routes import router as setup_router  # type: ignore
    app.include_router(setup_router, prefix="/api/setup", tags=["setup"])
except Exception as e:
    logger.warning(f"Setup router not available yet; skipping include: {e}")

try:
    from src.devices.routes import router as devices_router  # type: ignore
    app.include_router(devices_router, prefix="/api/devices", tags=["devices"])
except Exception:
    logger.warning("Devices router not available yet; skipping include")

try:
    from src.cluster.routes import router as cluster_router  # type: ignore
    app.include_router(cluster_router, prefix="/api/cluster", tags=["cluster"])
except Exception:
    logger.warning("Cluster router not available yet; skipping include")

try:
    from src.stations.routes import router as stations_router  # type: ignore
    app.include_router(stations_router, prefix="/api/stations", tags=["stations"])
except Exception:
    logger.warning("Stations router not available yet; skipping include")

try:
    from src.users.routes import router as users_router  # type: ignore
    app.include_router(users_router, prefix="/api/users", tags=["users"])
except Exception as e:
    logger.warning(f"Users router not available yet; skipping include: {e}")
 