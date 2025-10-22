from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.auth.deps import get_current_user
from src.database.connection import SessionLocal
from src.cluster.service import get_metadata, ensure_default_metadata
from src.devices.crypto import generate_key_and_csr

router = APIRouter()

class DeviceIdentity(BaseModel):
    device_id: str
    serial_number: Optional[str] = None
    name: Optional[str] = None
    ip_address: Optional[str] = None
    node_role: str
    cluster_id: Optional[str] = None
    version: Optional[str] = None

class DeviceStatus(BaseModel):
    id: str
    name: str
    model: str
    location: str
    group: str
    station: Optional[str] = None
    status: str  # online, warning, offline
    health_score: int
    alerts: int
    storage_used: int
    fps: int
    last_seen: datetime
    temperature: int
    battery: int

class DeviceListResponse(BaseModel):
    total: int
    devices: List[DeviceStatus]

# Mock data for development
MOCK_DEVICES = [
    DeviceStatus(
        id="ct3d-001",
        name="Main Entrance Scanner",
        model="CT3D-Pro-V2",
        location="Main Entrance",
        group="Main Entrance",
        station="Station Alpha",
        status="online",
        health_score=98,
        alerts=2,
        storage_used=65,
        fps=30,
        last_seen=datetime.now(),
        temperature=42,
        battery=98
    ),
    DeviceStatus(
        id="ct3d-002",
        name="Security Checkpoint",
        model="CT3D-Pro-V2",
        location="Security Checkpoint",
        group="Security Checkpoint",
        station="Station Beta",
        status="warning",
        health_score=85,
        alerts=5,
        storage_used=78,
        fps=25,
        last_seen=datetime.now(),
        temperature=48,
        battery=85
    ),
    DeviceStatus(
        id="ct3d-003",
        name="Emergency Exit Monitor",
        model="CT3D-Lite-V1",
        location="Emergency Exit",
        group="Emergency Exit",
        station="Station Gamma",
        status="offline",
        health_score=0,
        alerts=0,
        storage_used=92,
        fps=0,
        last_seen=datetime.now(),
        temperature=0,
        battery=0
    ),
    DeviceStatus(
        id="ct3d-004",
        name="Loading Dock Scanner A",
        model="CT3D-Pro-V2",
        location="Loading Dock",
        group="Loading Dock",
        station="Station Delta",
        status="online",
        health_score=95,
        alerts=1,
        storage_used=55,
        fps=30,
        last_seen=datetime.now(),
        temperature=44,
        battery=95
    ),
    DeviceStatus(
        id="ct3d-005",
        name="Staff Entry Monitor",
        model="CT3D-Lite-V1",
        location="Staff Entry",
        group="Staff Entry",
        station="Station Echo",
        status="online",
        health_score=88,
        alerts=0,
        storage_used=72,
        fps=25,
        last_seen=datetime.now(),
        temperature=41,
        battery=88
    )
]

@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    group: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get all devices with optional filtering"""
    devices = MOCK_DEVICES.copy()
    
    if group and group != "All Groups":
        devices = [d for d in devices if d.group == group]
    
    if status and status != "All Status":
        devices = [d for d in devices if d.status == status]
    
    return DeviceListResponse(total=len(devices), devices=devices)

@router.get("/info", response_model=DeviceIdentity)
async def device_info(current_user = Depends(get_current_user)):
    """Report local device identity/state (from setup metadata)."""
    with SessionLocal() as db:
        ensure_default_metadata(db)
        return DeviceIdentity(
            device_id=get_metadata(db, "device_id") or "device-stub",
            serial_number="serial-stub",
            name=get_metadata(db, "device_name") or "CTHz Node",
            ip_address="0.0.0.0",
            node_role=get_metadata(db, "node_role") or "unconfigured",
            cluster_id=get_metadata(db, "cluster_id"),
            version="0.1.0",
        )

@router.get("/{device_id}", response_model=DeviceStatus)
async def get_device(device_id: str, current_user = Depends(get_current_user)):
    """Get a specific device by ID"""
    device = next((d for d in MOCK_DEVICES if d.id == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.post("/{device_id}/scan")
async def start_scan(device_id: str, current_user = Depends(get_current_user)):
    """Start a scan on a specific device"""
    device = next((d for d in MOCK_DEVICES if d.id == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.status == "offline":
        raise HTTPException(status_code=400, detail="Cannot start scan on offline device")
    
    return {"message": f"Scan started on {device.name}", "scan_id": f"scan_{device_id}_{int(datetime.now().timestamp())}"}

@router.post("/{device_id}/stop")
async def stop_scan(device_id: str, current_user = Depends(get_current_user)):
    """Stop a scan on a specific device"""
    device = next((d for d in MOCK_DEVICES if d.id == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {"message": f"Scan stopped on {device.name}"}

@router.get("/groups/list")
async def get_groups(current_user = Depends(get_current_user)):
    """Get list of all device groups"""
    groups = list(set(d.group for d in MOCK_DEVICES))
    return {"groups": ["All Groups"] + groups}

@router.get("/stats/summary")
async def get_device_stats(current_user = Depends(get_current_user)):
    """Get device statistics summary"""
    total_devices = len(MOCK_DEVICES)
    online_devices = len([d for d in MOCK_DEVICES if d.status == "online"])
    warning_devices = len([d for d in MOCK_DEVICES if d.status == "warning"])
    offline_devices = len([d for d in MOCK_DEVICES if d.status == "offline"])
    total_alerts = sum(d.alerts for d in MOCK_DEVICES)
    
    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "warning_devices": warning_devices,
        "offline_devices": offline_devices,
        "total_alerts": total_alerts,
        "avg_health_score": int(sum(d.health_score for d in MOCK_DEVICES) / total_devices) if total_devices > 0 else 0
    } 


# Pairing-related stubs (manual IP discovery and info)

# (moved /info endpoint above to avoid shadowing by /{device_id})

class ManualDiscoverRequest(BaseModel):
    ip_address: str

@router.post("/discover/manual")
async def manual_device_discovery(req: ManualDiscoverRequest, current_user = Depends(get_current_user)):
    """Manually check a device by IP (stub)."""
    return {
        "discovered": True,
        "device": {
            "device_id": "device-stub-remote",
            "serial_number": "serial-remote",
            "name": "CTHz Remote",
            "ip_address": req.ip_address,
            "node_role": "unconfigured",
            "cluster_id": None,
            "version": "0.1.0",
        },
        "can_pair": True,
    }

class PairInitiateRequest(BaseModel):
    target_ip: str

@router.post("/pair/initiate")
async def initiate_pairing(req: PairInitiateRequest, current_user = Depends(get_current_user)):
    """Initiate pairing with a target device (stub)."""
    # This will call the remote device in manager flow; kept stub here
    return {"status": "initiated", "target_ip": req.target_ip}


class PairingRequest(BaseModel):
    pairing_token: str
    manager_endpoint: str | None = None
    manager_ca_fp: str | None = None


@router.post("/pair/request")
async def accept_pairing_request(body: PairingRequest):
    """Accept pairing request: generate CSR and return it."""
    # TODO: verify token claims against manager/cluster
    with SessionLocal() as db:
        ensure_default_metadata(db)
        cluster_id = get_metadata(db, "cluster_id") or "cluster-pending"
        device_id = get_metadata(db, "device_id") or "device-stub"
        key_pem, csr_pem = generate_key_and_csr("CTHz Node", device_id, cluster_id)
        # For MVP store the key in metadata (later move to secure storage)
        # NOTE: avoid huge strings in metadata in production
        return {
            "csr_pem": csr_pem.decode(),
            "device_id": device_id,
            "cluster_id": cluster_id,
            "name": get_metadata(db, "device_name") or "CTHz Node",
        }


class InstallCertRequest(BaseModel):
    device_cert_pem: str
    ca_cert_pem: str
    expires_at: datetime
    manager_endpoint: Optional[str] = None


@router.post("/pair/install-cert")
async def install_cert(req: InstallCertRequest):
    """Install device certificate (MVP: accept and pretend success)."""
    # TODO: persist certs, switch to mTLS client
    # After install, immediately send heartbeat to manager (no mTLS yet)
    if req.manager_endpoint:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                await client.post(
                    f"{req.manager_endpoint.rstrip('/')}/api/cluster/heartbeat",
                    json={
                        "device_id": "device-stub",
                        "status": {"installed": True},
                        "time": datetime.utcnow().isoformat(),
                    },
                )
        except Exception:
            pass
    return {"status": "installed", "node_role": "member", "heartbeat_interval_s": 30}