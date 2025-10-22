from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.auth.deps import get_current_user, require_role
from jose import jwt
from src.auth.auth import ALGORITHM
from src.config.settings import Settings
from src.database.connection import SessionLocal
from src.cluster.service import get_metadata, set_metadata, ensure_default_metadata
from src.cluster.crypto import generate_ca
from src.cluster.models import PairingToken, PairedDevice
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import NameOID
import uuid


router = APIRouter()
settings = Settings()


class DeviceIdentity(BaseModel):
    device_id: str
    serial_number: Optional[str] = None
    name: Optional[str] = None
    ip_address: Optional[str] = None
    node_role: str  # unconfigured | manager | member
    cluster_id: Optional[str] = None
    version: Optional[str] = None


class PairingTokenRequest(BaseModel):
    target_device_id: Optional[str] = None
    target_ip: Optional[str] = None


class PairingTokenResponse(BaseModel):
    token: str
    exp: datetime
    cluster_id: str
    jti: str


class CSRPayload(BaseModel):
    csr_pem: str
    device_id: str
    cluster_id: str
    name: Optional[str] = None


class CertBundle(BaseModel):
    device_cert_pem: str
    ca_cert_pem: str
    expires_at: datetime


class HeartbeatRequest(BaseModel):
    device_id: str
    status: Optional[Dict[str, Any]] = None
    time: datetime = Field(default_factory=datetime.utcnow)


@router.post("/pairing-token", response_model=PairingTokenResponse)
async def create_pairing_token(
    req: PairingTokenRequest,
    current_user = Depends(require_role("owner", "admin"))
):
    """Generate a short-lived pairing token with claims and persist jti."""
    now = datetime.utcnow()
    exp = now + timedelta(minutes=10)
    jti = str(uuid.uuid4())
    with SessionLocal() as db:
        ensure_default_metadata(db)
        cluster_id = get_metadata(db, "cluster_id") or "cluster-stub"
        # Persist token metadata
        db.add(PairingToken(
            token=jti,
            source_device_id=None,
            target_device_id=req.target_device_id,
            cluster_id=cluster_id,
            expires_at=exp,
            used=False,
        ))
        db.commit()
    claims = {
        "iss": "manager",
        "aud": "device",
        "sub": "pairing",
        "cluster_id": cluster_id,
        "jti": jti,
        "exp": int(exp.timestamp()),
        "target_ip": req.target_ip,
        "target_device_id": req.target_device_id,
    }
    # Symmetric signing for now using app secret; can migrate to ES256 later
    token = jwt.encode(claims, settings.secret_key, algorithm=ALGORITHM)
    return PairingTokenResponse(token=token, exp=exp, cluster_id=cluster_id, jti=jti)


@router.post("/pair")
async def pair_device_via_manager(
    body: Dict[str, Any],
    request: Request,
    current_user = Depends(require_role("owner", "admin"))
):
    """Manual IP pairing flow: token -> device CSR -> sign -> install."""
    print("pair_device_via_manager")
    import httpx
    target_ip = body.get("target_ip")
    if not target_ip:
        raise HTTPException(status_code=400, detail="target_ip required")
    # Allow passing host:port. If port is not provided, default to 8000.
    if ":" in target_ip:
        device_base = f"http://{target_ip}"
    else:
        device_base = f"http://{target_ip}:8000"
    # Prevent pairing if already paired with this IP
    with SessionLocal() as db:
        existing = db.query(PairedDevice).filter(PairedDevice.ip_address == target_ip).first()
        if existing:
            raise HTTPException(status_code=409, detail="Device already paired")

    # 1) Create pairing token
    token_resp = await create_pairing_token(PairingTokenRequest(target_ip=target_ip), current_user)  # type: ignore
    token = token_resp.token
    # 2) Ask device for CSR
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:  # TODO: enable TLS pinning
            r = await client.post(
                f"{device_base}/api/devices/pair/request",
                json={"pairing_token": token},
            )
            r.raise_for_status()
            device_csr = r.json()
    except Exception as e:
        raise HTTPException(status_code=408, detail=f"Device CSR request failed: {e}")
    # 3) Sign CSR
    cert_bundle = await sign_csr(CSRPayload(**device_csr))  # type: ignore
    # 4) Install cert on device
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:  # TODO: enable TLS pinning
            r = await client.post(
                f"{device_base}/api/devices/pair/install-cert",
                json={
                    "device_cert_pem": cert_bundle.device_cert_pem,
                    "ca_cert_pem": cert_bundle.ca_cert_pem,
                    "expires_at": cert_bundle.expires_at.isoformat(),
                    # Use base URL like http://host:port (no trailing slash)
                    "manager_endpoint": str(request.base_url).rstrip("/")
                },
            )
            r.raise_for_status()
            install_result = r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device cert install failed: {e}")
    # 5) Capture friendly name from CSR payload when provided (no extra call)
    device_name: Optional[str] = device_csr.get("name")
    # Persist/update paired device record
    with SessionLocal() as db:
        ensure_default_metadata(db)
        cluster_id = get_metadata(db, "cluster_id")
        device_id = device_csr.get("device_id", "unknown")
        pd = db.query(PairedDevice).filter(PairedDevice.device_id == device_id).first()
        if pd:
            pd.ip_address = target_ip
            pd.role = "member"
            pd.cluster_id = cluster_id
            pd.last_seen = datetime.utcnow()
            if not pd.paired_at:
                pd.paired_at = datetime.utcnow()
        else:
            pd = PairedDevice(
                device_id=device_id,
                ip_address=target_ip,
                role="member",
                cluster_id=cluster_id,
                paired_at=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )
            db.add(pd)
        db.commit()
        # Persist friendly name mapping if available
        if device_name:
            try:
                set_metadata(db, f"paired_name:{device_id}", device_name)
            except Exception:
                pass
    return {
        "status": install_result.get("status", "paired"),
        "relationship": "manager",
        "device": {
            "ip_address": target_ip,
            "device_id": device_csr.get("device_id", "unknown"),
        },
    }


@router.post("/sign-csr", response_model=CertBundle)
async def sign_csr(payload: CSRPayload):
    """Sign device CSR with cluster CA and return certificate bundle."""
    # TODO: validate pairing token jti via header in real flow
    with SessionLocal() as db:
        ensure_default_metadata(db)
        ca_cert_pem = get_metadata(db, "ca_cert_pem")
        ca_key_pem = get_metadata(db, "ca_key_pem")
        if not ca_cert_pem or not ca_key_pem:
            # Auto-bootstrap CA on first use
            try:
                cert_pem, key_pem, fp = generate_ca()
                set_metadata(db, "ca_cert_pem", cert_pem.decode() if hasattr(cert_pem, "decode") else cert_pem)
                set_metadata(db, "ca_key_pem", key_pem.decode() if hasattr(key_pem, "decode") else key_pem)
                set_metadata(db, "ca_fingerprint", fp)
                ca_cert_pem = get_metadata(db, "ca_cert_pem")
                ca_key_pem = get_metadata(db, "ca_key_pem")
            except Exception:
                raise HTTPException(status_code=409, detail="CA not initialized")
        ca_cert = x509.load_pem_x509_certificate(ca_cert_pem.encode())
        ca_key = load_pem_private_key(ca_key_pem.encode(), password=None)
        # Load CSR
        csr = x509.load_pem_x509_csr(payload.csr_pem.encode())
        # Build cert
        now = datetime.utcnow()
        builder = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=60))
        )
        # Add SAN with device_id and cluster_id if present
        try:
            san = x509.SubjectAlternativeName([
                x509.DNSName(f"device:{payload.device_id}"),
                x509.DNSName(f"cluster:{payload.cluster_id}"),
            ])
            builder = builder.add_extension(san, critical=False)
        except Exception:
            pass
        device_cert = builder.sign(private_key=ca_key, algorithm=hashes.SHA256())
        device_cert_pem = device_cert.public_bytes(serialization.Encoding.PEM).decode()
        return CertBundle(
            device_cert_pem=device_cert_pem,
            ca_cert_pem=ca_cert_pem,
            expires_at=now + timedelta(days=60),
        )


@router.post("/heartbeat")
async def heartbeat(req: HeartbeatRequest):
    """Receive member heartbeat (stub)."""
    # NOTE: enforce mTLS in production
    with SessionLocal() as db:
        pd = db.query(PairedDevice).filter(PairedDevice.device_id == req.device_id).first()
        if pd:
            pd.last_seen = req.time or datetime.utcnow()
            db.commit()
    return {"ok": True}


@router.get("/devices")
async def list_cluster_devices(request: Request, current_user = Depends(get_current_user)):
    """List paired devices with last seen and optional live status probe.

    Query params:
        live=true: perform http probe to /api/devices/info on each device in parallel.
    """
    from anyio import create_task_group
    import httpx

    live = request.query_params.get("live", "false").lower() == "true"
    with SessionLocal() as db:
        rows = db.query(PairedDevice).all()
        devices: List[Dict[str, Any]] = []
        now = datetime.utcnow()

        # base info from DB
        for row in rows:
            computed = "offline"
            if row.last_seen:
                delta = (now - row.last_seen).total_seconds()
                computed = "online" if delta < 120 else "warning" if delta < 600 else "offline"
            # Try to load persisted friendly name (captured at pairing)
            friendly_name = get_metadata(db, f"paired_name:{row.device_id}")
            devices.append({
                "device_id": row.device_id,
                "ip_address": row.ip_address,
                "role": row.role,
                "cluster_id": row.cluster_id,
                "paired_at": row.paired_at.isoformat() if row.paired_at else None,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                "status": computed,
                "status_color": "green" if computed == "online" else ("yellow" if computed == "warning" else "red"),
                # display_name will be enriched during live probe when possible
                "display_name": friendly_name or row.device_id,
            })

        # Also include the manager itself as an imaging device in the list (virtual entry)
        try:
            from urllib.parse import urlparse
            ensure_default_metadata(db)
            manager_device_id = get_metadata(db, "device_id") or "manager"
            manager_display_name = get_metadata(db, "device_name") or manager_device_id
            # Determine server host:port from the incoming request base_url
            parsed = urlparse(str(request.base_url))
            manager_hostport = parsed.netloc or "localhost:8000"
            devices.insert(0, {
                "device_id": manager_device_id,
                "ip_address": manager_hostport,
                "role": "manager",
                "cluster_id": get_metadata(db, "cluster_id"),
                "paired_at": None,
                "last_seen": now.isoformat(),
                "status": "online",
                "status_color": "green",
                "display_name": manager_display_name,
            })
        except Exception:
            # If for any reason we can't determine manager info, skip adding
            pass

    if not live or not devices:
        return {"devices": devices}

    # Live probe in parallel (best-effort; do not fail the whole call)
    async def probe_one(idx: int, device: Dict[str, Any]):
        base = device.get("ip_address") or ""
        if not base:
            return
        # Build base host:port
        base_host = base if ":" in base else f"{base}:8000"
        healthz_url = f"http://{base_host}/healthz"
        info_url = f"http://{base_host}/api/devices/info"
        try:
            async with httpx.AsyncClient(timeout=3.0, verify=False) as client:
                # Prefer unauthenticated health endpoint
                r = await client.get(healthz_url)
                if r.status_code == 200:
                    device["status"] = "online"
                    device["status_color"] = "green"
                    return
                # Fallback to devices/info; consider 200 or 401 as server alive
                r2 = await client.get(info_url)
                if r2.status_code in (200, 401):
                    device["status"] = "online"
                    device["status_color"] = "green"
                    # If JSON returned, use its friendly name when available
                    if r2.headers.get("content-type", "").startswith("application/json"):
                        try:
                            info = r2.json()
                            if isinstance(info, dict) and info.get("name"):
                                device["display_name"] = info["name"]
                        except Exception:
                            pass
        except Exception:
            # keep existing status
            pass

    # run probes
    async with create_task_group() as tg:
        for i, d in enumerate(devices):
            tg.start_soon(probe_one, i, d)

    return {"devices": devices}


@router.delete("/devices/{device_id}")
async def revoke_device(device_id: str, current_user = Depends(get_current_user)):
    """Unpair device: remove from DB (MVP)."""
    with SessionLocal() as db:
        row = db.query(PairedDevice).filter(PairedDevice.device_id == device_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Device not found")
        db.delete(row)
        db.commit()
    return {"ok": True, "revoked": True}


@router.get("/devices/{device_id}")
async def get_cluster_device(device_id: str, request: Request, current_user = Depends(get_current_user)):
    """Get a single paired device details with optional live probe (?live=true)."""
    import httpx
    with SessionLocal() as db:
        row = db.query(PairedDevice).filter(PairedDevice.device_id == device_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Device not found")
        now = datetime.utcnow()
        status = "offline"
        if row.last_seen:
            delta = (now - row.last_seen).total_seconds()
            status = "online" if delta < 120 else "warning" if delta < 600 else "offline"
        data: Dict[str, Any] = {
            "device_id": row.device_id,
            "ip_address": row.ip_address,
            "role": row.role,
            "cluster_id": row.cluster_id,
            "paired_at": row.paired_at.isoformat() if row.paired_at else None,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            "status": status,
            "status_color": "green" if status == "online" else ("yellow" if status == "warning" else "red"),
        }

    if request.query_params.get("live", "false").lower() != "true" or not data.get("ip_address"):
        return data

    base = data["ip_address"]
    url = f"http://{base}/api/devices/info" if ":" in base else f"http://{base}:8000/api/devices/info"
    try:
        async with httpx.AsyncClient(timeout=3.0, verify=False) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data["status"] = "online"
                data["status_color"] = "green"
    except Exception:
        pass
    return data


@router.get("/.well-known/cluster-ca")
async def get_cluster_ca():
    """Return cluster CA certificate and fingerprint (stub)."""
    with SessionLocal() as db:
        ensure_default_metadata(db)
        cluster_id = get_metadata(db, "cluster_id")
        ca_cert_pem = get_metadata(db, "ca_cert_pem")
        ca_fingerprint = get_metadata(db, "ca_fingerprint")
        return {
            "cluster_id": cluster_id or "",
            "ca_cert_pem": ca_cert_pem or "",
            "ca_fingerprint": ca_fingerprint or "",
        }


@router.post("/bootstrap-ca")
async def bootstrap_ca(current_user = Depends(require_role("owner", "admin"))):
    """Create cluster_id and CA if not present; return CA info."""
    with SessionLocal() as db:
        ensure_default_metadata(db)
        cluster_id = get_metadata(db, "cluster_id")
        if not cluster_id:
            # Very simple cluster id; replace with UUID in full implementation
            cluster_id = f"cluster-{int(datetime.utcnow().timestamp())}"
            set_metadata(db, "cluster_id", cluster_id)

        ca_cert_pem = get_metadata(db, "ca_cert_pem")
        ca_key_pem = get_metadata(db, "ca_key_pem")
        ca_fingerprint = get_metadata(db, "ca_fingerprint")
        if not (ca_cert_pem and ca_key_pem and ca_fingerprint):
            cert_pem, key_pem, fp = generate_ca()
            set_metadata(db, "ca_cert_pem", cert_pem.decode())
            set_metadata(db, "ca_key_pem", key_pem.decode())
            set_metadata(db, "ca_fingerprint", fp)
            ca_cert_pem, ca_key_pem, ca_fingerprint = cert_pem.decode(), key_pem.decode(), fp

        return {
            "cluster_id": cluster_id,
            "ca_cert_pem": ca_cert_pem,
            "ca_fingerprint": ca_fingerprint,
        }


@router.get("/devices/{device_id}/info")
async def proxy_device_info(device_id: str, request: Request, current_user = Depends(get_current_user)):
    """Proxy to a device's /api/devices/info using the same Authorization header.

    - If the target is the manager itself, proxy to local /api/devices/info
    - For members, forward to http://host:port/api/devices/info (default port 8000)
    """
    import httpx
    # Capture inbound Authorization header (JWT) to forward
    auth_header = request.headers.get("authorization")

    # Determine manager device id for special-case local proxy
    with SessionLocal() as db:
        ensure_default_metadata(db)
        manager_device_id = get_metadata(db, "device_id") or "manager"
        # If manager requested, call local API
        if device_id == manager_device_id:
            # Build local base from request
            from urllib.parse import urlparse
            parsed = urlparse(str(request.base_url))
            base = parsed.netloc or "localhost:8000"
            url = f"http://{base}/api/devices/info"
            try:
                async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                    r = await client.get(url, headers={"Authorization": auth_header} if auth_header else None)
                    r.raise_for_status()
                    return r.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"Manager info error: {e}")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Manager info request failed: {e}")

        # Lookup member device to get its host
        row = db.query(PairedDevice).filter(PairedDevice.device_id == device_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Device not found")
        target = row.ip_address or ""

    base_host = target if ":" in target else f"{target}:8000"
    url = f"http://{base_host}/api/devices/info"
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:  # TODO: enable TLS pinning
            r = await client.get(url, headers={"Authorization": auth_header} if auth_header else None)
            # Consider 200 as success; for 401, bubble up to explain auth issue
            if r.status_code == 200:
                return r.json()
            if r.headers.get("content-type", "").startswith("application/json"):
                try:
                    detail = r.json()
                except Exception:
                    detail = {"detail": r.text[:200]}
            else:
                detail = {"detail": r.text[:200]}
            raise HTTPException(status_code=r.status_code, detail=detail)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Device info error: {e}")
    except Exception as e:
        # Fallback: try healthz to at least report reachability
        try:
            async with httpx.AsyncClient(timeout=3.0, verify=False) as client:
                hz = await client.get(f"http://{base_host}/healthz")
                return {
                    "device_id": device_id,
                    "ip_address": target,
                    "reachable": hz.status_code == 200,
                    "error": str(e),
                }
        except Exception:
            raise HTTPException(status_code=502, detail=f"Device unreachable and info proxy failed: {e}")


