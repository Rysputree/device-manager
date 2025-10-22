from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.auth.models import User
from src.devices.models import Device
from src.stations.models import Station
from src.policies.models import Policy
from src.monitoring.models import Alert
from src.auth.deps import get_current_user
from src.cluster.service import ensure_default_metadata, set_metadata

router = APIRouter()


class NetworkConfigRequest(BaseModel):
    mode: str
    wifi_enabled: bool
    setup_mode: str
    ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    security: Optional[str] = None


class DeviceConfigRequest(BaseModel):
    device_name: str
    device_model: str
    group_name: str
    location: str
    setup_mode: str


class SetupCompleteRequest(BaseModel):
    setup_mode: str


@router.post("/network")
async def configure_network(config: NetworkConfigRequest):
    """Configure network settings for the device"""
    try:
        # Here you would implement the actual network configuration
        # For now, we'll just return success
        
        if config.setup_mode == "join":
            # For join mode, we might want to discover existing devices
            # or validate network connectivity
            pass
        else:
            # For new installation, configure as primary device
            pass
            
        return {"ok": True, "message": "Network configured successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Network configuration failed: {str(e)}")


@router.post("/device")
async def configure_device(config: DeviceConfigRequest):
    """Configure device information"""
    try:
        # Persist device metadata for name/model/location/group
        db = SessionLocal()
        try:
            ensure_default_metadata(db)
            set_metadata(db, "device_name", config.device_name)
            set_metadata(db, "device_model", config.device_model)
            set_metadata(db, "device_location", config.location)
            set_metadata(db, "device_group", config.group_name)
            # Optionally mark role hint based on setup mode
            role_hint = "member" if config.setup_mode == "join" else "manager"
            set_metadata(db, "node_role", role_hint)
        finally:
            db.close()

        return {"ok": True, "message": "Device configured successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device configuration failed: {str(e)}")


@router.post("/complete")
async def complete_setup():
    """Complete the setup process"""
    try:
        # Here you would implement the final setup steps
        # For now, we'll just return success with redirect info
        
        return {
            "ok": True, 
            "message": "Setup completed successfully",
            "redirect": "/login"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup completion failed: {str(e)}")


@router.post("/reset")
async def reset_system(current_user: dict = Depends(get_current_user)):
    """Reset the system to initial setup state (for testing/development)"""
    try:
        # Only allow owner role to reset the system
        if current_user.get("role") != "owner":
            raise HTTPException(status_code=403, detail="Only owners can reset the system")
        
        db = SessionLocal()
        try:
            # Delete all data in reverse dependency order
            db.query(Alert).delete()
            db.query(Policy).delete()
            db.query(Station).delete()
            db.query(Device).delete()
            db.query(User).delete()
            
            # Commit the transaction
            db.commit()
            
            return {
                "ok": True,
                "message": "System reset successfully. All data has been cleared."
            }
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System reset failed: {str(e)}")