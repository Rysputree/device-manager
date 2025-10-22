"""
Single Device Mode Service
Handles automatic creation of default group and station for single-device deployments
"""
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.groups.models import Group
from src.stations.models import Station
from src.devices.models import Device
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class SingleDeviceService:
    """Service for managing single-device mode operations"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def ensure_default_entities(self) -> tuple[Group, Station, Device]:
        """Ensure default group, station, and device exist for single-device mode"""
        try:
            # Get or create default group
            group = self.db.query(Group).filter(
                Group.name == settings.default_group_name
            ).first()
            
            if not group:
                group = Group(
                    name=settings.default_group_name,
                    description="Default group for single-device deployment",
                    location="Local Device"
                )
                self.db.add(group)
                self.db.commit()
                self.db.refresh(group)
                logger.info(f"Created default group: {group.name}")
            
            # Get or create default station
            station = self.db.query(Station).filter(
                Station.name == settings.default_station_name,
                Station.group_id == group.id
            ).first()
            
            if not station:
                station = Station(
                    group_id=group.id,
                    name=settings.default_station_name,
                    location="Local Device Station",
                    device_count=0,
                    max_devices=1,  # Single device mode
                    coverage_angle=360,
                    status="active"
                )
                self.db.add(station)
                self.db.commit()
                self.db.refresh(station)
                logger.info(f"Created default station: {station.name}")
            
            # Get or create default device
            device = self.db.query(Device).filter(
                Device.group_id == group.id,
                Device.station_id == station.id
            ).first()
            
            if not device:
                device = Device(
                    device_id="local-device-001",
                    name="CTHz System 300",
                    model="CTHz-300",
                    serial_number="CTHZ-300-001",
                    group_id=group.id,
                    station_id=station.id,
                    device_role="manager",  # Single device is always manager
                    location="Local Device",
                    status="offline",  # Will be updated when CTHz app connects
                    discovery_enabled=False,  # Not needed for single device
                    ssid_broadcast=False
                )
                self.db.add(device)
                self.db.commit()
                self.db.refresh(device)
                logger.info(f"Created default device: {device.name}")
            
            # Update station device count
            station.device_count = 1
            station.manager_device_id = device.id
            self.db.commit()
            
            return group, station, device
            
        except Exception as e:
            logger.error(f"Failed to ensure default entities: {e}")
            self.db.rollback()
            raise
        finally:
            self.db.close()
    
    def get_device_info(self) -> dict:
        """Get information about the single device"""
        try:
            device = self.db.query(Device).filter(
                Device.device_id == "local-device-001"
            ).first()
            
            if not device:
                return {"error": "Default device not found"}
            
            return {
                "device_id": device.device_id,
                "name": device.name,
                "model": device.model,
                "serial_number": device.serial_number,
                "status": device.status,
                "location": device.location,
                "last_seen": device.last_seen,
                "firmware_version": device.firmware_version,
                "hardware_version": device.hardware_version
            }
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {"error": str(e)}
        finally:
            self.db.close()
    
    def update_device_status(self, status: str, **kwargs) -> bool:
        """Update the single device status and other fields"""
        try:
            device = self.db.query(Device).filter(
                Device.device_id == "local-device-001"
            ).first()
            
            if not device:
                return False
            
            device.status = status
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
            
            self.db.commit()
            logger.info(f"Updated device status to: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            self.db.rollback()
            return False
        finally:
            self.db.close()

# Global service instance
single_device_service = SingleDeviceService()
