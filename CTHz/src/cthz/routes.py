"""
CTHz Hardware Layer API Routes
Direct communication with CTHz application running on same device
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
import logging
from src.cthz.client import CTHzClient
from src.cthz.single_device import single_device_service
from src.auth.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def cthz_health():
    """Check CTHz application health"""
    try:
        async with CTHzClient() as client:
            health_data = await client.health_check()
            return {
                "status": "healthy",
                "cthz_app": health_data,
                "device_manager": "online"
            }
    except Exception as e:
        logger.error(f"CTHz health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"CTHz application unavailable: {str(e)}")

@router.get("/device-info")
async def get_device_info(current_user = Depends(get_current_user)):
    """Get device identification information"""
    try:
        async with CTHzClient() as client:
            device_info = await client.get_device_info()
            
            # Update our database with latest info
            single_device_service.update_device_status(
                status="online",
                firmware_version=device_info.get("firmware_version"),
                hardware_version=device_info.get("hardware_version")
            )
            
            return device_info
    except Exception as e:
        logger.error(f"Failed to get device info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status(current_user = Depends(get_current_user)):
    """Get current operational state"""
    try:
        async with CTHzClient() as client:
            status = await client.get_status()
            
            # Update device status in our database
            device_status = status.get("status", "unknown")
            single_device_service.update_device_status(status=device_status)
            
            return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan/start")
async def start_scan(
    scan_params: Optional[Dict[str, Any]] = None,
    current_user = Depends(get_current_user)
):
    """Initiate threat detection scan"""
    try:
        async with CTHzClient() as client:
            result = await client.start_scan(scan_params)
            
            # Log scan initiation
            logger.info(f"Scan started by user {current_user.username}: {result}")
            
            return result
    except Exception as e:
        logger.error(f"Failed to start scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan/stop")
async def stop_scan(current_user = Depends(get_current_user)):
    """Stop current scan"""
    try:
        async with CTHzClient() as client:
            result = await client.stop_scan()
            
            # Log scan stop
            logger.info(f"Scan stopped by user {current_user.username}")
            
            return result
    except Exception as e:
        logger.error(f"Failed to stop scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans/{scan_id}")
async def get_scan_results(
    scan_id: str,
    current_user = Depends(get_current_user)
):
    """Retrieve scan results by ID"""
    try:
        async with CTHzClient() as client:
            results = await client.get_scan_results(scan_id)
            return results
    except Exception as e:
        logger.error(f"Failed to get scan results for {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans/recent")
async def get_recent_scans(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Query recent scans"""
    try:
        async with CTHzClient() as client:
            scans = await client.get_recent_scans(limit)
            return scans
    except Exception as e:
        logger.error(f"Failed to get recent scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calibration/start")
async def start_calibration(current_user = Depends(get_current_user)):
    """Start device calibration"""
    try:
        async with CTHzClient() as client:
            result = await client.start_calibration()
            
            # Log calibration start
            logger.info(f"Calibration started by user {current_user.username}")
            
            return result
    except Exception as e:
        logger.error(f"Failed to start calibration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calibration/{cal_id}")
async def get_calibration_results(
    cal_id: str,
    current_user = Depends(get_current_user)
):
    """Get calibration results"""
    try:
        async with CTHzClient() as client:
            results = await client.get_calibration_results(cal_id)
            return results
    except Exception as e:
        logger.error(f"Failed to get calibration results for {cal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/motion/status")
async def get_motion_status(current_user = Depends(get_current_user)):
    """Get motion detection state"""
    try:
        async with CTHzClient() as client:
            status = await client.get_motion_status()
            return status
    except Exception as e:
        logger.error(f"Failed to get motion status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/device")
async def get_device_config(current_user = Depends(get_current_user)):
    """Get device configuration"""
    try:
        async with CTHzClient() as client:
            config = await client.get_device_config()
            return config
    except Exception as e:
        logger.error(f"Failed to get device config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/device")
async def update_device_config(
    config: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update device configuration"""
    try:
        async with CTHzClient() as client:
            result = await client.update_device_config(config)
            
            # Log configuration change
            logger.info(f"Device config updated by user {current_user.username}")
            
            return result
    except Exception as e:
        logger.error(f"Failed to update device config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/logs")
async def get_system_logs(
    lines: int = 100,
    current_user = Depends(get_current_user)
):
    """Get diagnostic logs"""
    try:
        async with CTHzClient() as client:
            logs = await client.get_system_logs(lines)
            return {"logs": logs}
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream/rtsp")
async def get_rtsp_url(current_user = Depends(get_current_user)):
    """Get RTSP stream URL for video streaming"""
    try:
        async with CTHzClient() as client:
            rtsp_url = client.get_rtsp_stream_url()
            return {"rtsp_url": rtsp_url}
    except Exception as e:
        logger.error(f"Failed to get RTSP URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
