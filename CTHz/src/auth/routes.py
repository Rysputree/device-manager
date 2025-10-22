from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from src.auth.auth import authenticate_user, create_access_token, hash_password
from src.config.settings import Settings
from src.auth.deps import get_current_user, require_role
from src.auth.models import User
from src.database.connection import SessionLocal
from src.auth.validation import validate_password_strength

router = APIRouter()
settings = Settings()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in_hours: int


class SetupOwnerRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    confirm_password: str
    email: str = None


@router.post("/setup")
async def setup_owner(req: SetupOwnerRequest):
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    ok, msg = validate_password_strength(req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    with SessionLocal() as db:
        # If any user exists, setup already done
        existing = db.query(User).count()
        if existing > 0:
            raise HTTPException(status_code=409, detail="Already initialized")
        user = User(
            username=req.username, 
            password_hash=hash_password(req.password), 
            role="owner", 
            is_active=True,
            email=req.email
        )
        db.add(user)
        db.commit()
    return {"ok": True}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login time
    with SessionLocal() as db:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            db_user.last_login = datetime.utcnow()
            db.commit()
    
    token = create_access_token(user.username, user.role, settings.access_token_exp_hours)
    return TokenResponse(access_token=token, role=user.role, expires_in_hours=settings.access_token_exp_hours)


@router.get("/me")
async def me(user=Depends(get_current_user)):
    """Get current user details including email"""
    with SessionLocal() as db:
        db_user = db.query(User).filter(User.username == user["sub"]).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "username": db_user.username, 
            "role": db_user.role,
            "email": db_user.email,
            "is_active": db_user.is_active
        }


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    """Logout user (invalidate token on client side)"""
    return {"ok": True, "message": "Logged out successfully"}


@router.get("/admin-only")
async def admin_only(user=Depends(require_role("owner", "admin"))):
    return {"ok": True, "user": user["sub"], "role": user["role"]} 