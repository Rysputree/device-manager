from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

# Define role-based permissions for each module
PERMISSIONS = {
    "dashboard": {
        "owner": "full",
        "admin": "full", 
        "monitor": "read_only"
    },
    "discovery": {
        "owner": "full",
        "admin": "full",
        "monitor": "no_access"
    },
    "devices": {
        "owner": "full",
        "admin": "full",
        "monitor": "read_only"
    },
    "monitoring": {
        "owner": "full",
        "admin": "full",
        "monitor": "read_only"
    },
    "policies": {
        "owner": "full",
        "admin": "full",
        "monitor": "read_only"
    },
    "alerts": {
        "owner": "full",
        "admin": "full",
        "monitor": "read_only"
    },
    "configuration": {
        "owner": "full",
        "admin": "limited",
        "monitor": "no_access"
    },
    "storage": {
        "owner": "full",
        "admin": "limited",
        "monitor": "read_only"
    },
    "audit": {
        "owner": "full",
        "admin": "limited",
        "monitor": "no_access"
    },
    "users": {
        "owner": "full",
        "admin": "limited",
        "monitor": "no_access"
    },
    "errors": {
        "owner": "full",
        "admin": "full",
        "monitor": "read_only"
    }
}

class RBACMiddleware(BaseHTTPMiddleware):
    """Role-Based Access Control Middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip RBAC for certain paths
        skip_paths = [
            "/healthz",
            "/login",
            "/setup",
            "/api/auth/login",
            "/api/auth/setup",
            "/api/setup/",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Extract user role from request (this would be set by auth middleware)
        user_role = getattr(request.state, 'user_role', None)
        
        if not user_role:
            # If no user role, redirect to login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login")
        
        # Check permissions for the requested module
        module = self._extract_module_from_path(request.url.path)
        if module and module in PERMISSIONS:
            permission = PERMISSIONS[module].get(user_role, "no_access")
            
            if permission == "no_access":
                raise HTTPException(status_code=403, detail="Access denied: Insufficient permissions")
            
            # Store permission level in request state for use in route handlers
            request.state.permission_level = permission
        
        response = await call_next(request)
        return response
    
    def _extract_module_from_path(self, path: str) -> str:
        """Extract module name from URL path"""
        # Remove leading slash and split by /
        parts = path.lstrip('/').split('/')
        
        if not parts or parts[0] == '':
            return None
        
        # Map URL paths to module names
        module_mapping = {
            "dashboard": "dashboard",
            "discovery": "discovery", 
            "devices": "devices",
            "monitoring": "monitoring",
            "policies": "policies",
            "alerts": "alerts",
            "configuration": "configuration",
            "storage": "storage",
            "audit": "audit",
            "users": "users",
            "errors": "errors"
        }
        
        return module_mapping.get(parts[0])

