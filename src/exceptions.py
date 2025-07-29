"""Custom exceptions for platform-specific operations"""

class PlatformError(Exception):
    """Base exception for platform-specific errors"""
    pass

class DeviceError(PlatformError):
    """Base exception for device-related errors"""
    pass

class LocationError(PlatformError):
    """Base exception for location-related errors"""
    pass

# iOS-specific exceptions
class iOSDeviceError(DeviceError):
    """iOS device-specific error"""
    pass

class iOSLocationError(LocationError):
    """iOS location-specific error"""
    pass

class iOSTunnelError(iOSDeviceError):
    """iOS tunnel connection error"""
    pass

class iOSDeveloperModeError(iOSDeviceError):
    """iOS developer mode error"""
    pass

# Android-specific exceptions
class AndroidDeviceError(DeviceError):
    """Android device-specific error"""
    pass

class AndroidLocationError(LocationError):
    """Android location-specific error"""
    pass

class AndroidADBError(AndroidDeviceError):
    """Android ADB connection error"""
    pass

class AndroidMockLocationError(AndroidLocationError):
    """Android mock location permission error"""
    pass

# Platform detection exceptions
class PlatformNotSupportedError(PlatformError):
    """Platform not supported error"""
    pass

class PlatformToolMissingError(PlatformError):
    """Required platform tool not available"""
    pass 