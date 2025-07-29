from abc import ABC, abstractmethod
from src.platform_detector import list_all_devices
from src.exceptions import PlatformNotSupportedError, PlatformToolMissingError
from src.config import setup_logging

logger = setup_logging()

def validate_coordinates(lat, lng):
    """Validate latitude and longitude coordinates"""
    try:
        lat_float = float(lat)
        lng_float = float(lng)
        
        if not (-90 <= lat_float <= 90):
            return False, 'Latitude must be between -90 and 90'
        
        if not (-180 <= lng_float <= 180):
            return False, 'Longitude must be between -180 and 180'
            
        return True, (lat_float, lng_float)
    except ValueError:
        return False, 'Invalid coordinate format'

class LocationServiceInterface(ABC):
    """Abstract interface for platform-specific location services"""
    
    @abstractmethod
    def set_location(self, device_id, lat, lng):
        """Set device location to specified coordinates"""
        pass
    
    @abstractmethod
    def clear_location(self, device_id):
        """Clear simulated location"""
        pass
    
    @abstractmethod
    def get_current_location(self, device_id):
        """Get current device location if available"""
        pass

class LocationServiceFactory:
    """Factory for creating platform-specific location services"""
    
    @staticmethod
    def create(platform):
        """Create location service for specified platform"""
        if platform == 'ios':
            from src.ios.ios_location_service import iOSLocationService
            return iOSLocationService()
        elif platform == 'android':
            from src.android.android_location_service import AndroidLocationService
            return AndroidLocationService()
        else:
            raise PlatformNotSupportedError(f"Platform '{platform}' not supported")

# Global location service instances
_location_services = {}

def get_location_service(platform):
    """Get or create location service for platform"""
    if platform not in _location_services:
        _location_services[platform] = LocationServiceFactory.create(platform)
    return _location_services[platform]

def find_device_platform(device_id):
    """Find platform for a given device ID"""
    devices_result = list_all_devices()
    if devices_result['success']:
        for device in devices_result['devices']:
            if device['id'] == device_id:
                return device['platform']
    return None

# Unified API functions (backwards compatible with existing code)
def set_location(lat, lng, device_id=None, platform=None):
    """Set location using platform-specific service"""
    # Validate coordinates first
    is_valid, validation_result = validate_coordinates(lat, lng)
    if not is_valid:
        return {
            'success': False,
            'message': validation_result
        }
    
    lat_float, lng_float = validation_result
    
    # Determine device and platform
    target_device_id = device_id
    target_platform = platform
    
    # If no device specified, try to get from stored connection info
    if not target_device_id:
        # Try to get device from iOS tunnel info (backwards compatibility)
        try:
            from src.ios.ios_location_service import iOSLocationService
            ios_service = iOSLocationService()
            tunnel_info = ios_service.get_tunnel_info()
            if tunnel_info and len(tunnel_info) >= 3:
                target_device_id = tunnel_info[2]
                target_platform = 'ios'
        except Exception:
            pass
    
    # If still no device, return error
    if not target_device_id:
        return {
            'success': False,
            'message': 'No device connected. Please connect a device first by clicking on a device card.'
        }
    
    # Determine platform if not specified
    if not target_platform:
        target_platform = find_device_platform(target_device_id)
        if not target_platform:
            return {
                'success': False,
                'message': f'Could not determine platform for device {target_device_id}'
            }
    
    try:
        service = get_location_service(target_platform)
        return service.set_location(target_device_id, lat_float, lng_float)
    except (PlatformNotSupportedError, PlatformToolMissingError) as e:
        return {
            'success': False,
            'message': str(e)
        }

def clear_location(device_id=None, platform=None):
    """Clear location using platform-specific service"""
    # Determine device and platform
    target_device_id = device_id
    target_platform = platform
    
    # If no device specified, try to get from stored connection info
    if not target_device_id:
        # Try to get device from iOS tunnel info (backwards compatibility)
        try:
            from src.ios.ios_location_service import iOSLocationService
            ios_service = iOSLocationService()
            tunnel_info = ios_service.get_tunnel_info()
            if tunnel_info and len(tunnel_info) >= 3:
                target_device_id = tunnel_info[2]
                target_platform = 'ios'
        except Exception:
            pass
    
    # If still no device, return error
    if not target_device_id:
        return {
            'success': False,
            'message': 'No device connected. Please connect a device first by clicking on a device card.'
        }
    
    # Determine platform if not specified
    if not target_platform:
        target_platform = find_device_platform(target_device_id)
        if not target_platform:
            return {
                'success': False,
                'message': f'Could not determine platform for device {target_device_id}'
            }
    
    try:
        service = get_location_service(target_platform)
        return service.clear_location(target_device_id)
    except (PlatformNotSupportedError, PlatformToolMissingError) as e:
        return {
            'success': False,
            'message': str(e)
        } 