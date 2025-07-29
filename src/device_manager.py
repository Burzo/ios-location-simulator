from abc import ABC, abstractmethod
from src.platform_detector import list_all_devices
from src.exceptions import PlatformNotSupportedError, PlatformToolMissingError
from src.config import setup_logging

logger = setup_logging()

class DeviceManagerInterface(ABC):
    """Abstract interface for platform-specific device managers"""
    
    @abstractmethod
    def list_devices(self):
        """List connected devices for this platform"""
        pass
    
    @abstractmethod
    def connect_device(self, device_id):
        """Connect and setup device for location testing"""
        pass
    
    @abstractmethod
    def disconnect_device(self, device_id=None):
        """Disconnect device and cleanup connections"""
        pass
    
    @abstractmethod
    def check_device_status(self, device_id):
        """Check device connection status"""
        pass

class DeviceManagerFactory:
    """Factory for creating platform-specific device managers"""
    
    @staticmethod
    def create(platform):
        """Create device manager for specified platform"""
        if platform == 'ios':
            from src.ios.ios_device_manager import iOSDeviceManager
            return iOSDeviceManager()
        elif platform == 'android':
            from src.android.android_device_manager import AndroidDeviceManager
            return AndroidDeviceManager()
        else:
            raise PlatformNotSupportedError(f"Platform '{platform}' not supported")

# Global device manager instances
_device_managers = {}

def get_device_manager(platform):
    """Get or create device manager for platform"""
    if platform not in _device_managers:
        _device_managers[platform] = DeviceManagerFactory.create(platform)
    return _device_managers[platform]

# Unified API functions (backwards compatible with existing code)
def list_devices():
    """List all connected devices across all platforms"""
    return list_all_devices()

def connect_device(device_id, platform=None):
    """Connect to device using platform-specific manager"""
    if not device_id:
        return {
            'success': False,
            'message': 'Device ID is required. Please select a device first.'
        }
    
    # If platform not specified, try to detect from device list
    if not platform:
        devices_result = list_all_devices()
        if devices_result['success']:
            for device in devices_result['devices']:
                if device['id'] == device_id:
                    platform = device['platform']
                    break
        
        if not platform:
            return {
                'success': False,
                'message': f'Could not determine platform for device {device_id}'
            }
    
    try:
        manager = get_device_manager(platform)
        return manager.connect_device(device_id)
    except (PlatformNotSupportedError, PlatformToolMissingError) as e:
        return {
            'success': False,
            'message': str(e)
        }

def cleanup_existing_connections():
    """Clean up connections across all platforms"""
    logger.info("Cleaning up existing connections across all platforms...")
    
    # Try to cleanup iOS connections
    try:
        ios_manager = get_device_manager('ios')
        ios_manager.disconnect_device()
    except Exception as e:
        logger.debug(f"iOS cleanup failed: {e}")
    
    # Try to cleanup Android connections
    try:
        android_manager = get_device_manager('android')
        android_manager.disconnect_device()
    except Exception as e:
        logger.debug(f"Android cleanup failed: {e}")
    
    logger.info("Multi-platform cleanup completed") 