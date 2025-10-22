from typing import Literal, Optional
from fastapi import Depends, HTTPException, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.auth.auth import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = creds.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return payload


async def get_current_user_from_cookie(request: Request, access_token: Optional[str] = Cookie(None)) -> dict:
    """Get current user from JWT token stored in cookie for web pages"""
    # Debug: Print cookie value
    print(f"DEBUG: access_token cookie: {access_token}")
    print(f"DEBUG: All cookies: {request.cookies}")
    
    # Try to get token from Authorization header as fallback for Safari
    auth_header = request.headers.get("authorization")
    if not access_token and auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]  # Remove "Bearer " prefix
        print(f"DEBUG: Using token from Authorization header: {access_token[:20]}...")
    
    # Try to get token from query parameter as fallback for Safari
    if not access_token:
        access_token = request.query_params.get("token")
        if access_token:
            print(f"DEBUG: Using token from query parameter: {access_token[:20]}...")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized - No access token cookie, header, or query param")
    
    try:
        payload = decode_token(access_token)
        print(f"DEBUG: Decoded payload: {payload}")
    except Exception as e:
        print(f"DEBUG: Token decode error: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid token")
    
    if "sub" not in payload or "role" not in payload:
        print(f"DEBUG: Missing sub or role in payload: {payload}")
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid token payload")
    
    return payload


def require_role(*allowed: Literal["owner", "admin", "monitor"]):
    async def _checker(user: dict = Depends(get_current_user)) -> dict:
        role = user.get("role")
        if role not in allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _checker 