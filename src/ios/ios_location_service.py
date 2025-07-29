from src.location_service import LocationServiceInterface
from src.ios.ios_process_utils import run_pymobiledevice3_command
from src.config import setup_logging

logger = setup_logging()

class iOSLocationService(LocationServiceInterface):
    """iOS-specific location service implementation"""
    
    def get_tunnel_info(self):
        """Read tunnel info from file"""
        logger.debug("Reading tunnel info from /tmp/tunnel_info.txt")
        tunnel_info = run_pymobiledevice3_command('cat /tmp/tunnel_info.txt')
        
        if not tunnel_info['success'] or not tunnel_info['output'].strip():
            return None, None, None
        
        parts = tunnel_info['output'].strip().split()
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]  # address, port, device_id
        
        return None, None, None
    
    def set_location_via_tunnel(self, tunnel_address, tunnel_port, device_id, lat, lng):
        """Set location using tunnel connection for iOS 18.x"""
        logger.info(f"Using tunnel connection for device {device_id}: {tunnel_address}:{tunnel_port}")
        logger.debug(f"Tunnel location command: --rsd {tunnel_address} {tunnel_port}")
        command = f'python3 -m pymobiledevice3 developer dvt simulate-location set --rsd {tunnel_address} {tunnel_port} --udid {device_id} -- {lat} {lng}'
        
        # Send command twice for better location confidence
        run_pymobiledevice3_command(command)
        result = run_pymobiledevice3_command(command)
        
        if result['success']:
            logger.info(f"Location set successfully via tunnel for device {device_id}: {lat}, {lng}")
            return {
                'success': True,
                'message': f'Location set to {lat}, {lng} via tunnel',
                'coordinates': {'latitude': float(lat), 'longitude': float(lng)}
            }
        else:
            logger.warning(f"Tunnel location command failed: {result.get('error', 'Unknown error')}")
            return None
    
    def set_location_fallback(self, device_id, lat, lng):
        """Set location using fallback methods without tunnel"""
        if device_id:
            logger.info(f"Attempting location set for device {device_id} without tunnel...")
            command = f'python3 -m pymobiledevice3 developer dvt simulate-location set --udid {device_id} -- {lat} {lng}'
        else:
            logger.warning("No device ID found, using default device")
            command = f'python3 -m pymobiledevice3 developer dvt simulate-location set -- {lat} {lng}'
        
        # Send command twice for better location confidence
        run_pymobiledevice3_command(command)
        result = run_pymobiledevice3_command(command)
        
        if not result['success']:
            logger.info("Attempting legacy location command...")
            if device_id:
                command = f'python3 -m pymobiledevice3 developer simulate-location set --udid {device_id} -- {lat} {lng}'
            else:
                command = f'python3 -m pymobiledevice3 developer simulate-location set -- {lat} {lng}'
            
            # Send legacy command twice for better location confidence
            run_pymobiledevice3_command(command)
            result = run_pymobiledevice3_command(command)
        
        return result
    
    def set_location(self, device_id, lat, lng):
        """Set iOS device location to specified coordinates"""
        if not device_id:
            return {
                'success': False,
                'message': 'No device connected. Please connect a device first by clicking on a device card.'
            }
        
        # Get tunnel info
        tunnel_address, tunnel_port, stored_device_id = self.get_tunnel_info()
        
        # Use stored device ID if provided device_id doesn't match
        if stored_device_id and stored_device_id != device_id:
            logger.warning(f"Device ID mismatch: requested {device_id}, stored {stored_device_id}. Using stored ID.")
            device_id = stored_device_id
        
        # Try tunnel connection first if available
        if tunnel_address != 'pending' and tunnel_port != 'pending' and tunnel_address and tunnel_port:
            tunnel_result = self.set_location_via_tunnel(tunnel_address, tunnel_port, device_id, lat, lng)
            if tunnel_result:
                return tunnel_result
        
        # Try fallback methods
        result = self.set_location_fallback(device_id, lat, lng)
        
        if result['success']:
            logger.info(f"Location set successfully: {lat}, {lng}")
            return {
                'success': True,
                'message': f'Location set to {lat}, {lng}',
                'coordinates': {'latitude': float(lat), 'longitude': float(lng)}
            }
        else:
            logger.error(f"All location setting attempts failed: {result.get('error', 'Unknown error')}")
            error_msg = result['error']
            if 'InvalidServiceError' in error_msg:
                error_msg = 'Location service unavailable. Try: 1) Click "Connect & Setup" again, 2) Ensure iPhone passcode is disabled, 3) Restart your iPhone if needed.'
            elif 'DeveloperDiskImage' in error_msg:
                error_msg = 'DeveloperDiskImage not mounted. Click "Connect & Setup" first.'
            
            return {
                'success': False,
                'message': 'Failed to set location: ' + error_msg
            }
    
    def clear_location_via_tunnel(self, tunnel_address, tunnel_port, device_id):
        """Clear location using tunnel connection for iOS 18.x"""
        logger.info(f"Clearing location via tunnel for device {device_id}: {tunnel_address}:{tunnel_port}")
        result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 developer dvt simulate-location clear --rsd {tunnel_address} {tunnel_port} --udid {device_id}')
        
        if result['success']:
            logger.info(f"Location cleared successfully via tunnel for device {device_id}")
            return {
                'success': True,
                'message': 'Location simulation cleared via tunnel'
            }
        else:
            logger.warning(f"Tunnel location clear failed: {result.get('error', 'Unknown error')}")
            return None
    
    def clear_location_fallback(self, device_id):
        """Clear location using fallback methods without tunnel"""
        if device_id:
            logger.info(f"Attempting to clear location for device {device_id} without tunnel...")
            result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 developer dvt simulate-location clear --udid {device_id}')
        else:
            logger.warning("No device ID found, using default device")
            result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 developer dvt simulate-location clear')
        
        if not result['success']:
            logger.info("Attempting legacy location clear command...")
            if device_id:
                result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 developer simulate-location clear --udid {device_id}')
            else:
                result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 developer simulate-location clear')
        
        return result
    
    def clear_location(self, device_id):
        """Clear iOS device location simulation"""
        if not device_id:
            return {
                'success': False,
                'message': 'No device connected. Please connect a device first by clicking on a device card.'
            }
        
        logger.info("Attempting to clear iOS location simulation...")
        
        # Get tunnel info
        tunnel_address, tunnel_port, stored_device_id = self.get_tunnel_info()
        
        # Use stored device ID if provided device_id doesn't match
        if stored_device_id and stored_device_id != device_id:
            logger.warning(f"Device ID mismatch: requested {device_id}, stored {stored_device_id}. Using stored ID.")
            device_id = stored_device_id
        
        # Try tunnel connection first if available
        if tunnel_address != 'pending' and tunnel_port != 'pending' and tunnel_address and tunnel_port:
            tunnel_result = self.clear_location_via_tunnel(tunnel_address, tunnel_port, device_id)
            if tunnel_result:
                return tunnel_result
        
        # Try fallback methods
        result = self.clear_location_fallback(device_id)
        
        if result['success']:
            logger.info("Location cleared successfully")
            return {
                'success': True,
                'message': 'Location simulation cleared'
            }
        else:
            logger.error(f"All location clearing attempts failed: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'message': 'Failed to clear location: ' + result['error']
            }
    
    def get_current_location(self, device_id):
        """Get current iOS device location if available"""
        # iOS doesn't provide an easy way to get current simulated location
        # This would require additional implementation
        return {
            'success': False,
            'message': 'Getting current location not implemented for iOS'
        } 