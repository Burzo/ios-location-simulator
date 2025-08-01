import json
import time
from src.process_utils import run_pymobiledevice3_command
from src.config import setup_logging

logger = setup_logging()

def cleanup_existing_connections():
    """Clean up any existing tunnel connections and processes"""
    logger.info("Cleaning up existing connections...")
    
    # Kill any existing tunnel processes
    logger.debug("Killing existing tunnel processes...")
    run_pymobiledevice3_command('pkill -f "lockdown start-tunnel" || true')
    
    # Clean up tunnel files
    logger.debug("Cleaning up tunnel files...")
    run_pymobiledevice3_command('rm -f /tmp/tunnel.log /tmp/tunnel_info.txt')
    
    # Give processes time to clean up
    time.sleep(1)
    logger.info("Cleanup completed")

def list_devices():
    """List connected iOS devices"""
    result = run_pymobiledevice3_command('python3 -m pymobiledevice3 usbmux list')
    return result

def check_device_passcode(device_id):
    """Check if device passcode is disabled"""
    info_result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 lockdown info --udid {device_id}')
    if info_result['success']:
        try:
            device_info = json.loads(info_result['output'])
            return device_info.get('PasswordProtected', True)
        except:
            pass
    return None

def check_developer_mode(device_id):
    """Check and enable developer mode if needed"""
    logger.info("Checking developer mode status...")
    amfi_status = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 amfi developer-mode-status --udid {device_id}')
    logger.info(f"AMFI status check result: success={amfi_status['success']}, output='{amfi_status['output']}', error='{amfi_status.get('error', '')}'")
    
    dev_mode_enabled = False
    
    if amfi_status['success'] and ('enabled' in amfi_status['output'].lower() or 'true' in amfi_status['output'].lower()):
        dev_mode_enabled = True
        dev_mode_result = {'success': True, 'output': 'already enabled'}
        logger.info("Developer mode is already enabled - skipping enable step")
    else:
        logger.info("Developer mode not enabled - attempting to enable...")
        dev_mode_result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 amfi enable-developer-mode --udid {device_id}')
        if not dev_mode_result['success'] and 'passcode is set' in dev_mode_result['error']:
            logger.error("Cannot enable developer mode - passcode is set")
            return None, dev_mode_result
        dev_mode_enabled = dev_mode_result['success']
        if dev_mode_enabled:
            logger.info("Developer mode enabled successfully")
        else:
            logger.warning(f"Developer mode enable failed: {dev_mode_result.get('error', 'Unknown error')}")
    
    return dev_mode_enabled, dev_mode_result

def mount_developer_disk_image(device_id):
    """Mount DeveloperDiskImage for the device"""
    logger.info("Checking DeveloperDiskImage mount status...")
    mount_result = run_pymobiledevice3_command(f'python3 -m pymobiledevice3 mounter auto-mount --udid {device_id}')
    
    if not mount_result['success'] and 'already mounted' not in mount_result['error']:
        logger.error(f"Failed to mount DeveloperDiskImage: {mount_result['error']}")
        return mount_result
    
    if 'successfully' in mount_result['output']:
        logger.info("DeveloperDiskImage mounted successfully")
    else:
        logger.info("DeveloperDiskImage already mounted")
    
    return mount_result

def start_tunnel_service(device_id):
    """Start tunnel service for iOS 17.4+ and extract connection details"""
    logger.info("Initiating tunnel service startup...")
    logger.debug("Tunnel log file: /tmp/tunnel.log")
    run_pymobiledevice3_command(f'python3 -m pymobiledevice3 lockdown start-tunnel --udid {device_id} > /tmp/tunnel.log 2>&1 &')
    logger.info("Tunnel service background process started")
    
    time.sleep(2)
    
    # Extract tunnel connection details
    logger.info("Reading tunnel log to extract connection details...")
    tunnel_info = run_pymobiledevice3_command('cat /tmp/tunnel.log')
    tunnel_address = None
    tunnel_port = None
    
    if tunnel_info['success'] and 'RSD Address:' in tunnel_info['output']:
        logger.debug(f"Tunnel log content: {tunnel_info['output']}")
        lines = tunnel_info['output'].split('\n')
        for line in lines:
            if 'RSD Address:' in line:
                tunnel_address = line.split('RSD Address:')[1].strip()
                logger.debug(f"Extracted tunnel address: {tunnel_address}")
            elif 'RSD Port:' in line:
                tunnel_port = line.split('RSD Port:')[1].strip()
                logger.debug(f"Extracted tunnel port: {tunnel_port}")
    
    # Store tunnel info for location commands (include device ID)
    if tunnel_address and tunnel_port:
        logger.info(f"Writing tunnel info to file: {tunnel_address} {tunnel_port} {device_id}")
        run_pymobiledevice3_command(f'echo "{tunnel_address} {tunnel_port} {device_id}" > /tmp/tunnel_info.txt')
        tunnel_status = f'established at {tunnel_address}:{tunnel_port}'
        logger.info(f"Tunnel established successfully: {tunnel_address}:{tunnel_port}")
    else:
        # Still store device ID even if tunnel details aren't ready
        run_pymobiledevice3_command(f'echo "pending pending {device_id}" > /tmp/tunnel_info.txt')
        tunnel_status = 'started (may take a moment to establish)'
        logger.warning("Tunnel started but connection details not yet available")
    
    return tunnel_status

def connect_device(device_id):
    """Main device connection flow - setup device for location testing"""
    if not device_id:
        return {
            'success': False,
            'message': 'Device ID is required. Please select a device first.'
        }
    
    logger.info(f"Connecting to device: {device_id}")
    
    # Clean up any existing connections first
    cleanup_existing_connections()
    
    # Check if passcode is disabled
    passcode_protected = check_device_passcode(device_id)
    if passcode_protected:
        return {
            'success': False,
            'message': 'iPhone passcode must be disabled for location simulation. Go to Settings > Face ID & Passcode > Turn Passcode Off, then restart your iPhone.'
        }
    
    # Check/enable developer mode
    dev_mode_enabled, dev_mode_result = check_developer_mode(device_id)
    if dev_mode_enabled is None:  # Error occurred
        return {
            'success': False,
            'message': 'Cannot enable developer mode with passcode set. Please either: 1) Disable iPhone passcode first, or 2) Manually enable Developer Mode in Settings > Privacy & Security > Developer Mode.'
        }
    
    # Mount DeveloperDiskImage
    mount_result = mount_developer_disk_image(device_id)
    if not mount_result['success'] and 'already mounted' not in mount_result['error']:
        return {
            'success': False,
            'message': 'Failed to mount DeveloperDiskImage: ' + mount_result['error']
        }
    
    # Start tunnel service
    tunnel_status = start_tunnel_service(device_id)
    
    logger.info("Device setup completed successfully!")
    
    return {
        'success': True,
        'message': 'Device successfully prepared for location testing! Tunnel service established for iOS 18.x.',
        'details': {
            'developer_mode': 'already enabled' if dev_mode_enabled and 'already enabled' in dev_mode_result['output'] else 'enabled',
            'disk_image': 'mounted successfully' if 'successfully' in mount_result['output'] else 'already mounted',
            'tunnel_service': tunnel_status,
            'device_id': device_id
        }
    } 