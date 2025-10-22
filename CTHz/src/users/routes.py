from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.auth.models import User
from src.auth.deps import get_current_user
from src.auth.auth import hash_password
from src.auth.permissions import check_module_access
from datetime import datetime

router = APIRouter()


class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@router.get("/", response_model=List[UserResponse])
async def get_users(
    current_user: dict = Depends(check_module_access("users", "view")),
    db: Session = Depends(get_db)
):
    """Get all users (Owner and Admin only)"""
    
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        ) for user in users
    ]


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: dict = Depends(check_module_access("users", "create")),
    db: Session = Depends(get_db)
):
    """Create a new user (Owner and Admin only)"""
    
    # Validate role
    if user_data.role not in ["admin", "monitor"]:
        raise HTTPException(status_code=400, detail="Can only create admin or monitor users")
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        email=user_data.email,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        last_login=new_user.last_login
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(check_module_access("users", "view")),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (Owner and Admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: dict = Depends(check_module_access("users", "edit")),
    db: Session = Depends(get_db)
):
    """Update a user (Owner and Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Additional check: Admin cannot modify owner users
    if current_user.get("role") == "admin" and user.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot modify owner users")
    
    # Update fields if provided
    if user_data.username is not None:
        # Check if new username already exists
        existing_user = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = user_data.username
    
    if user_data.email is not None:
        user.email = user_data.email
    
    if user_data.role is not None:
        # Validate role change
        if user_data.role not in ["admin", "monitor"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(check_module_access("users", "delete")),
    db: Session = Depends(get_db)
):
    """Delete a user (Owner only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Additional check: Cannot delete owner users
    if user.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot delete owner users")
    
    db.delete(user)
    db.commit()
    
    return {"ok": True, "message": "User deleted successfully"}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str,
    current_user: dict = Depends(check_module_access("users", "edit")),
    db: Session = Depends(get_db)
):
    """Reset a user's password (Owner and Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Additional check: Admin cannot modify owner users
    if current_user.get("role") == "admin" and user.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot modify owner users")
    
    user.password_hash = hash_password(new_password)
    db.commit()
    
    return {"ok": True, "message": "Password reset successfully"}
