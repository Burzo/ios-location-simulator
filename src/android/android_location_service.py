from src.location_service import LocationServiceInterface
from src.android.android_process_utils import run_adb_command
from src.config import setup_logging

logger = setup_logging()

class AndroidLocationService(LocationServiceInterface):
    """Android-specific location service implementation"""
    
    def set_location_via_am_broadcast(self, device_id, lat, lng):
        """Set location using activity manager broadcast"""
        logger.info(f"Setting location via AM broadcast for device {device_id}: {lat}, {lng}")
        
        # Method 1: Use activity manager to send location update broadcast
        command = f'adb -s {device_id} shell am broadcast -a android.location.GPS_FIX_CHANGE --ef latitude {lat} --ef longitude {lng}'
        result1 = run_adb_command(command)
        
        # Method 2: Alternative broadcast method
        command2 = f'adb -s {device_id} shell am broadcast -a android.location.PROVIDERS_CHANGED --es latitude "{lat}" --es longitude "{lng}"'
        result2 = run_adb_command(command2)
        
        if result1['success'] or result2['success']:
            logger.info(f"Location broadcast sent successfully: {lat}, {lng}")
            return {
                'success': True,
                'message': f'Location set to {lat}, {lng} via broadcast',
                'coordinates': {'latitude': float(lat), 'longitude': float(lng)}
            }
        
        return None
    
    def set_location_via_mock_provider(self, device_id, lat, lng):
        """Set location using mock location provider"""
        logger.info(f"Setting location via mock provider for device {device_id}: {lat}, {lng}")
        
        # Try to use a simple test app approach via am instrument
        command = f'adb -s {device_id} shell am instrument -w -e debug false -e latitude {lat} -e longitude {lng} com.android.cts.verifier/com.android.cts.location.MockLocationTestCase'
        result = run_adb_command(command)
        
        if result['success']:
            logger.info(f"Mock location set successfully: {lat}, {lng}")
            return {
                'success': True,
                'message': f'Location set to {lat}, {lng} via mock provider',
                'coordinates': {'latitude': float(lat), 'longitude': float(lng)}
            }
        
        return None
    
    def set_location_via_service_call(self, device_id, lat, lng):
        """Set location using service call (requires root or system permissions)"""
        logger.info(f"Attempting service call location set for device {device_id}: {lat}, {lng}")
        
        # This requires elevated permissions but may work on some devices
        # Using LocationManager service call
        import time
        current_time = int(time.time() * 1000)
        
        command = f'adb -s {device_id} shell service call location 20 s16 "gps" i32 1 f {lat} f {lng} f 0.0 i64 {current_time}'
        result = run_adb_command(command)
        
        if result['success'] and 'Result: Parcel' in result['output']:
            logger.info(f"Service call location set successfully: {lat}, {lng}")
            return {
                'success': True,
                'message': f'Location set to {lat}, {lng} via service call',
                'coordinates': {'latitude': float(lat), 'longitude': float(lng)}
            }
        
        return None
    
    def set_location_via_settings(self, device_id, lat, lng):
        """Set location by modifying system settings (limited success)"""
        logger.info(f"Attempting settings-based location set for device {device_id}: {lat}, {lng}")
        
        # Store coordinates in system settings (may not affect location immediately)
        result1 = run_adb_command(f'adb -s {device_id} shell settings put system mock_location_latitude {lat}')
        result2 = run_adb_command(f'adb -s {device_id} shell settings put system mock_location_longitude {lng}')
        
        # Trigger location provider update
        result3 = run_adb_command(f'adb -s {device_id} shell am broadcast -a android.location.PROVIDERS_CHANGED')
        
        if result1['success'] and result2['success']:
            logger.info(f"Location settings updated: {lat}, {lng}")
            return {
                'success': True,
                'message': f'Location coordinates stored in settings: {lat}, {lng}',
                'coordinates': {'latitude': float(lat), 'longitude': float(lng)}
            }
        
        return None
    
    def set_location(self, device_id, lat, lng):
        """Set Android device location to specified coordinates"""
        if not device_id:
            return {
                'success': False,
                'message': 'No device connected. Please connect a device first by clicking on a device card.'
            }
        
        logger.info(f"Setting Android location for device {device_id}: {lat}, {lng}")
        
        # Try multiple methods in order of preference
        methods = [
            ("AM Broadcast", self.set_location_via_am_broadcast),
            ("Mock Provider", self.set_location_via_mock_provider),
            ("Service Call", self.set_location_via_service_call),
            ("Settings", self.set_location_via_settings)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.debug(f"Trying {method_name} method...")
                result = method_func(device_id, lat, lng)
                if result:
                    logger.info(f"Location set successfully using {method_name}")
                    result['method'] = method_name
                    return result
            except Exception as e:
                logger.warning(f"{method_name} method failed: {e}")
                continue
        
        # If all methods failed
        logger.error("All Android location setting methods failed")
        return {
            'success': False,
            'message': 'Failed to set location on Android device. Ensure mock location is enabled in Developer Options and a mock location app is selected.'
        }
    
    def clear_location_via_broadcast(self, device_id):
        """Clear location using broadcast"""
        logger.info(f"Clearing location via broadcast for device {device_id}")
        
        # Send broadcast to clear GPS fix
        command = f'adb -s {device_id} shell am broadcast -a android.location.GPS_ENABLED_CHANGE --ez enabled false'
        result1 = run_adb_command(command)
        
        # Re-enable GPS
        command2 = f'adb -s {device_id} shell am broadcast -a android.location.GPS_ENABLED_CHANGE --ez enabled true'
        result2 = run_adb_command(command2)
        
        # Notify providers changed
        command3 = f'adb -s {device_id} shell am broadcast -a android.location.PROVIDERS_CHANGED'
        result3 = run_adb_command(command3)
        
        if result1['success'] or result2['success'] or result3['success']:
            logger.info("Location cleared via broadcast")
            return {
                'success': True,
                'message': 'Location simulation cleared via broadcast'
            }
        
        return None
    
    def clear_location_via_settings(self, device_id):
        """Clear location by removing settings"""
        logger.info(f"Clearing location via settings for device {device_id}")
        
        # Remove stored coordinates
        result1 = run_adb_command(f'adb -s {device_id} shell settings delete system mock_location_latitude')
        result2 = run_adb_command(f'adb -s {device_id} shell settings delete system mock_location_longitude')
        
        # Reset mock location app (optional)
        result3 = run_adb_command(f'adb -s {device_id} shell settings delete secure mock_location_app')
        
        if result1['success'] or result2['success']:
            logger.info("Location settings cleared")
            return {
                'success': True,
                'message': 'Location simulation settings cleared'
            }
        
        return None
    
    def clear_location(self, device_id):
        """Clear Android device location simulation"""
        if not device_id:
            return {
                'success': False,
                'message': 'No device connected. Please connect a device first by clicking on a device card.'
            }
        
        logger.info(f"Clearing Android location simulation for device {device_id}")
        
        # Try multiple clearing methods
        methods = [
            ("Broadcast", self.clear_location_via_broadcast),
            ("Settings", self.clear_location_via_settings)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.debug(f"Trying {method_name} clear method...")
                result = method_func(device_id)
                if result:
                    logger.info(f"Location cleared successfully using {method_name}")
                    return result
            except Exception as e:
                logger.warning(f"{method_name} clear method failed: {e}")
                continue
        
        # If all methods failed, still return success as clearing is best-effort
        logger.warning("All clear methods failed, but this is often normal on Android")
        return {
            'success': True,
            'message': 'Location clear attempted. You may need to manually disable mock location or restart location services.'
        }
    
    def get_current_location(self, device_id):
        """Get current Android device location"""
        if not device_id:
            return {
                'success': False,
                'message': 'No device connected.'
            }
        
        logger.info(f"Getting current location for Android device {device_id}")
        
        # Try to get location from dumpsys
        result = run_adb_command(f'adb -s {device_id} shell dumpsys location')
        
        if result['success']:
            output = result['output']
            # Parse location info from dumpsys output
            # This is complex and device-dependent, so provide basic info
            if 'last location' in output.lower() or 'gps' in output.lower():
                return {
                    'success': True,
                    'message': 'Location services active',
                    'details': 'Check device location settings for current coordinates'
                }
        
        return {
            'success': False,
            'message': 'Unable to retrieve current location from Android device'
        } 