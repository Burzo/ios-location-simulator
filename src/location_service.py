from src.process_utils import run_pymobiledevice3_command
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

def get_tunnel_info():
    """Read tunnel info from file"""
    logger.debug("Reading tunnel info from /tmp/tunnel_info.txt")
    tunnel_info = run_pymobiledevice3_command('cat /tmp/tunnel_info.txt')
    
    if not tunnel_info['success'] or not tunnel_info['output'].strip():
        return None, None, None
    
    parts = tunnel_info['output'].strip().split()
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]  # address, port, device_id
    
    return None, None, None

def set_location_via_tunnel(tunnel_address, tunnel_port, device_id, lat, lng):
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

def set_location_fallback(device_id, lat, lng):
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

def set_location(lat, lng):
    """Main location setting function with all fallback logic"""
    # Validate coordinates
    is_valid, validation_result = validate_coordinates(lat, lng)
    if not is_valid:
        return {
            'success': False,
            'message': validation_result
        }
    
    lat_float, lng_float = validation_result
    
    # Get tunnel info
    tunnel_address, tunnel_port, device_id = get_tunnel_info()
    
    if not device_id:
        return {
            'success': False,
            'message': 'No device connected. Please connect a device first by clicking on a device card.'
        }
    
    # Try tunnel connection first if available
    if tunnel_address != 'pending' and tunnel_port != 'pending' and tunnel_address and tunnel_port:
        tunnel_result = set_location_via_tunnel(tunnel_address, tunnel_port, device_id, lat, lng)
        if tunnel_result:
            return tunnel_result
    
    # Try fallback methods
    result = set_location_fallback(device_id, lat, lng)
    
    if result['success']:
        logger.info(f"Location set successfully: {lat}, {lng}")
        return {
            'success': True,
            'message': f'Location set to {lat}, {lng}',
            'coordinates': {'latitude': lat_float, 'longitude': lng_float}
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

def clear_location_via_tunnel(tunnel_address, tunnel_port, device_id):
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

def clear_location_fallback(device_id):
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

def clear_location():
    """Main location clearing function with all fallback logic"""
    logger.info("Attempting to clear location simulation...")
    
    # Get tunnel info
    tunnel_address, tunnel_port, device_id = get_tunnel_info()
    
    if not device_id:
        return {
            'success': False,
            'message': 'No device connected. Please connect a device first by clicking on a device card.'
        }
    
    # Try tunnel connection first if available
    if tunnel_address != 'pending' and tunnel_port != 'pending' and tunnel_address and tunnel_port:
        tunnel_result = clear_location_via_tunnel(tunnel_address, tunnel_port, device_id)
        if tunnel_result:
            return tunnel_result
    
    # Try fallback methods
    result = clear_location_fallback(device_id)
    
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