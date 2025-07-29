from src.device_manager import DeviceManagerInterface
from src.android.android_process_utils import run_adb_command, check_adb_available, get_device_property
from src.config import setup_logging

logger = setup_logging()

class AndroidDeviceManager(DeviceManagerInterface):
    """Android-specific device manager implementation"""
    
    def list_devices(self):
        """List connected Android devices"""
        if not check_adb_available():
            return {
                'success': False,
                'output': '',
                'error': 'ADB not available. Please install Android SDK platform-tools.'
            }
        
        result = run_adb_command('adb devices -l')
        return result
    
    def check_device_status(self, device_id):
        """Check Android device connection status"""
        result = run_adb_command(f'adb -s {device_id} get-state')
        return result['success'] and 'device' in result['output']
    
    def check_usb_debugging(self, device_id):
        """Check if USB debugging is enabled"""
        # Try a simple adb command to see if device responds
        result = run_adb_command(f'adb -s {device_id} shell echo "test"')
        if result['success'] and 'test' in result['output']:
            return True
        return False
    
    def check_developer_options(self, device_id):
        """Check if Developer Options are enabled"""
        dev_enabled = get_device_property(device_id, 'ro.debuggable')
        dev_settings = run_adb_command(f'adb -s {device_id} shell settings get global development_settings_enabled')
        
        logger.info(f"Developer options check: debuggable={dev_enabled}, settings={dev_settings.get('output', '').strip()}")
        
        return {
            'debuggable': dev_enabled == '1',
            'settings_enabled': dev_settings.get('output', '').strip() == '1',
            'success': dev_settings['success']
        }
    
    def check_mock_location_settings(self, device_id):
        """Check mock location settings"""
        # Check if mock location is enabled
        mock_app = run_adb_command(f'adb -s {device_id} shell settings get secure mock_location_app')
        mock_enabled = run_adb_command(f'adb -s {device_id} shell settings get secure mock_location')
        
        logger.info(f"Mock location check: app={mock_app.get('output', '').strip()}, enabled={mock_enabled.get('output', '').strip()}")
        
        return {
            'mock_app': mock_app.get('output', '').strip(),
            'mock_enabled': mock_enabled.get('output', '').strip(),
            'success': mock_app['success'] and mock_enabled['success']
        }
    
    def enable_mock_location(self, device_id):
        """Enable mock location for shell (best effort)"""
        logger.info("Attempting to enable mock location...")
        
        # Try to set shell as mock location app
        result1 = run_adb_command(f'adb -s {device_id} shell settings put secure mock_location_app com.android.shell')
        
        # Try to enable mock location permission for shell
        result2 = run_adb_command(f'adb -s {device_id} shell appops set com.android.shell android:mock_location allow')
        
        # Alternative method - enable mock location globally (on some devices)
        result3 = run_adb_command(f'adb -s {device_id} shell settings put secure mock_location 1')
        
        success = result1['success'] or result2['success'] or result3['success']
        
        if success:
            logger.info("Mock location setup completed (some commands may have failed - this is normal)")
        else:
            logger.warning("Failed to enable mock location - manual setup may be required")
        
        return {
            'success': success,
            'shell_app': result1['success'],
            'appops': result2['success'],
            'global_setting': result3['success']
        }
    
    def check_location_services(self, device_id):
        """Check if location services are enabled"""
        location_enabled = run_adb_command(f'adb -s {device_id} shell settings get secure location_providers_allowed')
        gps_enabled = run_adb_command(f'adb -s {device_id} shell dumpsys location | grep -i "gps"')
        
        return {
            'providers': location_enabled.get('output', '').strip(),
            'gps_available': 'gps' in gps_enabled.get('output', '').lower(),
            'success': location_enabled['success']
        }
    
    def connect_device(self, device_id):
        """Main Android device connection flow - setup device for location testing"""
        if not device_id:
            return {
                'success': False,
                'message': 'Device ID is required. Please select a device first.'
            }
        
        logger.info(f"Connecting to Android device: {device_id}")
        
        # Check if ADB is available
        if not check_adb_available():
            return {
                'success': False,
                'message': 'ADB not available. Please install Android SDK platform-tools and ensure ADB is in your PATH.'
            }
        
        # Check device connection
        if not self.check_device_status(device_id):
            return {
                'success': False,
                'message': f'Device {device_id} not found or not accessible. Please ensure USB debugging is enabled and device is authorized.'
            }
        
        # Check USB debugging
        if not self.check_usb_debugging(device_id):
            return {
                'success': False,
                'message': 'USB debugging not working. Please enable Developer Options and USB Debugging, then authorize this computer on your device.'
            }
        
        # Check developer options
        dev_check = self.check_developer_options(device_id)
        if not dev_check['settings_enabled']:
            logger.warning("Developer Options may not be properly enabled")
        
        # Check and enable mock location
        mock_check = self.check_mock_location_settings(device_id)
        mock_setup = self.enable_mock_location(device_id)
        
        # Check location services
        location_check = self.check_location_services(device_id)
        
        # Get device info
        model = get_device_property(device_id, 'ro.product.model') or 'Unknown Android Device'
        android_version = get_device_property(device_id, 'ro.build.version.release') or 'Unknown'
        
        logger.info("Android device setup completed!")
        
        # Determine success based on critical checks
        setup_success = (
            dev_check['success'] and 
            location_check['success'] and 
            (mock_setup['success'] or mock_check['mock_app'])
        )
        
        message = f'Android device {model} (Android {android_version}) prepared for location testing!'
        if not mock_setup['success']:
            message += ' Note: Mock location may need manual setup in Settings > Developer Options > Mock Location App.'
        
        return {
            'success': setup_success,
            'message': message,
            'details': {
                'model': model,
                'android_version': android_version,
                'developer_options': 'enabled' if dev_check['settings_enabled'] else 'check manually',
                'mock_location': 'configured' if mock_setup['success'] else 'needs manual setup',
                'location_services': 'available' if location_check['gps_available'] else 'check manually',
                'device_id': device_id,
                'platform': 'android'
            }
        }
    
    def disconnect_device(self, device_id=None):
        """Clean up Android device connections"""
        logger.info("Cleaning up Android connections...")
        
        # Kill any ADB server connections (optional)
        # This is generally not needed unless there are connection issues
        # run_adb_command('adb kill-server')
        
        logger.info("Android cleanup completed") 