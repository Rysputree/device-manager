from fastapi import HTTPException, Depends
from typing import Literal
from src.auth.deps import get_current_user

PermissionLevel = Literal["full", "limited", "read_only", "no_access"]

def require_permission(required_level: PermissionLevel):
    """Dependency to require a specific permission level"""
    def permission_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        
        # Define role hierarchy
        role_hierarchy = {
            "owner": 4,  # Highest level
            "admin": 3,
            "monitor": 2,
            "guest": 1   # Lowest level
        }
        
        # Define permission level hierarchy
        permission_hierarchy = {
            "no_access": 0,
            "read_only": 1,
            "limited": 2,
            "full": 3
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_permission_level = permission_hierarchy.get(required_level, 0)
        
        if user_level < required_permission_level:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied: Requires {required_level} permission level"
            )
        
        return current_user
    
    return permission_checker

def require_owner():
    """Dependency to require owner role"""
    return require_permission("full")

def require_admin_or_owner():
    """Dependency to require admin or owner role"""
    def admin_or_owner_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Requires admin or owner role"
            )
        return current_user
    
    return admin_or_owner_checker

def require_read_access():
    """Dependency to require at least read access"""
    return require_permission("read_only")

def check_module_access(module: str, action: str = "view"):
    """Check if user has access to a specific module and action"""
    def module_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        
        # Module permissions based on the CSV
        module_permissions = {
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
        
        if module not in module_permissions:
            raise HTTPException(status_code=404, detail="Module not found")
        
        user_permission = module_permissions[module].get(user_role, "no_access")
        
        # Check if user has required permission for the action
        if action == "view" and user_permission == "no_access":
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: No access to {module} module"
            )
        elif action in ["create", "edit", "delete"] and user_permission not in ["full", "limited"]:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: Insufficient permissions for {action} action in {module} module"
            )
        elif action in ["create", "edit", "delete"] and user_permission == "limited" and module in ["configuration", "storage", "audit", "users"]:
            # Additional checks for limited access modules
            if module == "users" and action == "delete":
                # Only owners can delete users
                if user_role != "owner":
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: Only owners can delete users"
                    )
        
        return current_user
    
    return module_checker

