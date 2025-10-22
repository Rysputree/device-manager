from datetime import datetime, timedelta, timezone
from typing import Optional, Literal
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config.settings import Settings
from src.database.connection import SessionLocal
from src.auth.models import User

settings = Settings()

# Configure bcrypt with explicit backend to avoid detection issues
# Use pbkdf2_sha256 as fallback if bcrypt fails
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"], 
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__min_rounds=4,
    bcrypt__max_rounds=31,
    pbkdf2_sha256__default_rounds=29000
)
ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    # bcrypt has a 72-byte limit, so we truncate longer passwords
    # Convert to bytes, truncate to 72 bytes, then convert back to string
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    
    try:
        return pwd_context.hash(plain_password)
    except (ValueError, Exception) as e:
        if "password cannot be longer than 72 bytes" in str(e):
            # If still too long, truncate more aggressively
            plain_password = plain_password[:50]  # Truncate to 50 chars to be safe
            try:
                return pwd_context.hash(plain_password)
            except Exception:
                # If bcrypt still fails, use pbkdf2_sha256 as fallback
                from passlib.hash import pbkdf2_sha256
                return pbkdf2_sha256.hash(plain_password)
        elif "bcrypt" in str(e).lower():
            # If bcrypt fails for other reasons, use pbkdf2_sha256
            from passlib.hash import pbkdf2_sha256
            return pbkdf2_sha256.hash(plain_password)
        raise


def verify_password(plain_password: str, password_hash: str) -> bool:
    # Apply the same truncation as in hash_password to ensure consistency
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    
    try:
        return pwd_context.verify(plain_password, password_hash)
    except (ValueError, Exception) as e:
        if "password cannot be longer than 72 bytes" in str(e):
            # If still too long, truncate more aggressively
            plain_password = plain_password[:50]  # Truncate to 50 chars to be safe
            try:
                return pwd_context.verify(plain_password, password_hash)
            except Exception:
                # If bcrypt still fails, try pbkdf2_sha256
                from passlib.hash import pbkdf2_sha256
                return pbkdf2_sha256.verify(plain_password, password_hash)
        elif "bcrypt" in str(e).lower():
            # If bcrypt fails for other reasons, try pbkdf2_sha256
            from passlib.hash import pbkdf2_sha256
            return pbkdf2_sha256.verify(plain_password, password_hash)
        raise


def create_access_token(subject: str, role: Literal["owner", "admin", "monitor"], expires_hours: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(username: str, password: str) -> Optional[User]:
    with SessionLocal() as db:
        user = get_user_by_username(db, username)
        if not user or not verify_password(password, user.password_hash) or not user.is_active:
            return None
        return user 