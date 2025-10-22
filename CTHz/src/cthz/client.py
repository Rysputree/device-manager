"""
CTHz Hardware Layer API Client
Direct HTTPS communication with CTHz application running on same device
"""
import httpx
import ssl
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from src.config.settings import settings

logger = logging.getLogger(__name__)

class CTHzClient:
    """Client for communicating with CTHz hardware layer via HTTPS"""
    
    def __init__(self):
        self.base_url = settings.cthz_api_base_url
        self.timeout = settings.cthz_api_timeout
        self.rtsp_base_url = settings.cthz_rtsp_base_url
        
        # Configure SSL context for TLS communication
        self.ssl_context = ssl.create_default_context()
        if settings.verify_tls and settings.tls_ca_cert_path:
            self.ssl_context.load_verify_locations(settings.tls_ca_cert_path)
        else:
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # HTTP client with TLS configuration
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            verify=self.ssl_context if settings.verify_tls else False
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check CTHz application health"""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device identification information"""
        try:
            response = await self.client.get("/device-info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current operational state"""
        try:
            response = await self.client.get("/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise
    
    async def start_scan(self, scan_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiate threat detection scan"""
        try:
            payload = scan_params or {}
            response = await self.client.post("/scan/start", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to start scan: {e}")
            raise
    
    async def stop_scan(self) -> Dict[str, Any]:
        """Stop current scan"""
        try:
            response = await self.client.post("/scan/stop")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to stop scan: {e}")
            raise
    
    async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """Retrieve scan results by ID"""
        try:
            response = await self.client.get(f"/scans/{scan_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get scan results for {scan_id}: {e}")
            raise
    
    async def get_recent_scans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Query recent scans"""
        try:
            response = await self.client.get(f"/scans/recent?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get recent scans: {e}")
            raise
    
    async def start_calibration(self) -> Dict[str, Any]:
        """Start device calibration"""
        try:
            response = await self.client.post("/calibration/start")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to start calibration: {e}")
            raise
    
    async def get_calibration_results(self, cal_id: str) -> Dict[str, Any]:
        """Get calibration results"""
        try:
            response = await self.client.get(f"/calibration/{cal_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get calibration results for {cal_id}: {e}")
            raise
    
    async def get_motion_status(self) -> Dict[str, Any]:
        """Get motion detection state"""
        try:
            response = await self.client.get("/motion/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get motion status: {e}")
            raise
    
    async def get_device_config(self) -> Dict[str, Any]:
        """Get device configuration"""
        try:
            response = await self.client.get("/config/device")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get device config: {e}")
            raise
    
    async def update_device_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update device configuration"""
        try:
            response = await self.client.put("/config/device", json=config)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update device config: {e}")
            raise
    
    async def get_system_logs(self, lines: int = 100) -> List[str]:
        """Get diagnostic logs"""
        try:
            response = await self.client.get(f"/system/logs?lines={lines}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            raise
    
    def get_rtsp_stream_url(self, stream_type: str = "main") -> str:
        """Get RTSP stream URL for video streaming"""
        return f"{self.rtsp_base_url}/{stream_type}"

# Global client instance for dependency injection
cthz_client = CTHzClient()
