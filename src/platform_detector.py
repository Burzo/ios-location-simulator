import subprocess
import json
from src.config import setup_logging

logger = setup_logging()

def run_command(command, timeout=10):
    """Execute a command and return result safely"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Command timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

def detect_ios_devices():
    """Detect connected iOS devices using pymobiledevice3"""
    try:
        result = run_command('python3 -m pymobiledevice3 usbmux list')
        if result['success'] and result['output'].strip():
            devices = []
            try:
                # Try to parse as JSON first
                device_data = json.loads(result['output'])
                
                # Handle both single device (dict) and multiple devices (list)
                if isinstance(device_data, dict):
                    device_data = [device_data]
                elif isinstance(device_data, list):
                    pass  # Already a list
                else:
                    # If it's neither dict nor list, fall back to text parsing
                    raise ValueError("Unexpected data format")
                
                for device in device_data:
                    if isinstance(device, dict):
                        devices.append({
                            'id': device.get('Identifier') or device.get('UniqueDeviceID', 'unknown'),
                            'name': device.get('DeviceName', 'iOS Device'),
                            'platform': 'ios',
                            'connection_type': device.get('ConnectionType', 'usb').lower(),
                            'status': 'available',
                            # Store additional info for connection details
                            '_device_data': device
                        })
                        
            except (json.JSONDecodeError, ValueError):
                # Fall back to text parsing if JSON parsing fails
                logger.debug("JSON parsing failed, trying text parsing")
                devices = parse_ios_text_output(result['output'])
            
            return devices
        return []
    except Exception as e:
        logger.debug(f"iOS detection failed: {e}")
        return []

def parse_ios_text_output(output):
    """Parse iOS device output in text format as fallback"""
    devices = []
    lines = output.split('\n')
    
    # Look for structured output patterns
    current_device = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current_device and 'Identifier' in current_device:
                devices.append({
                    'id': current_device.get('Identifier', 'unknown'),
                    'name': current_device.get('DeviceName', 'iOS Device'),
                    'platform': 'ios',
                    'connection_type': current_device.get('ConnectionType', 'usb').lower(),
                    'status': 'available',
                    '_device_data': current_device
                })
                current_device = {}
            continue
            
        # Parse key-value pairs
        if ':' in line:
            key, value = line.split(':', 1)
            current_device[key.strip()] = value.strip()
        elif line.startswith('ConnectionType') and not current_device:
            # Skip header line
            continue
        else:
            # Try space-separated format as last resort
            parts = line.split()
            if len(parts) >= 2 and 'Identifier' not in current_device:
                current_device = {
                    'ConnectionType': parts[0] if len(parts) > 0 else 'USB',
                    'Identifier': parts[1] if len(parts) > 1 else 'unknown',
                    'DeviceName': ' '.join(parts[2:]) if len(parts) > 2 else 'iOS Device'
                }
    
    # Add any remaining device
    if current_device and 'Identifier' in current_device:
        devices.append({
            'id': current_device.get('Identifier', 'unknown'),
            'name': current_device.get('DeviceName', 'iOS Device'),
            'platform': 'ios',
            'connection_type': current_device.get('ConnectionType', 'usb').lower(),
            'status': 'available',
            '_device_data': current_device
        })
    
    return devices

def detect_android_devices():
    """Detect connected Android devices using ADB"""
    try:
        result = run_command('adb devices -l')
        if result['success'] and result['output'].strip():
            devices = []
            lines = result['output'].split('\n')
            for line in lines[1:]:  # Skip header line
                if line.strip() and ' device ' in line:
                    # Parse line format: "DEVICE_ID    device usb:1-1 product:... model:... device:..."
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'device':
                        device_id = parts[0]
                        
                        # Extract model from the remaining parts
                        model = 'Android Device'
                        for part in parts[2:]:
                            if part.startswith('model:'):
                                model = part.replace('model:', '').replace('_', ' ')
                                break
                        
                        devices.append({
                            'id': device_id,
                            'name': model,
                            'platform': 'android',
                            'connection_type': 'usb',
                            'status': 'available'
                        })
            return devices
        return []
    except Exception as e:
        logger.debug(f"Android detection failed: {e}")
        return []

def check_platform_requirements():
    """Check if required platform tools are available"""
    requirements = {
        'ios': False,
        'android': False
    }
    
    # Check for pymobiledevice3
    ios_check = run_command('python3 -m pymobiledevice3 --help')
    requirements['ios'] = ios_check['success']
    
    # Check for ADB
    android_check = run_command('adb version')
    requirements['android'] = android_check['success']
    
    return requirements

def list_all_devices():
    """List all connected devices across platforms"""
    logger.info("Detecting devices across all platforms...")
    
    devices = []
    requirements = check_platform_requirements()
    
    # Detect iOS devices if tool is available
    if requirements['ios']:
        ios_devices = detect_ios_devices()
        devices.extend(ios_devices)
        logger.info(f"Found {len(ios_devices)} iOS device(s)")
    else:
        logger.info("pymobiledevice3 not available - skipping iOS detection")
    
    # Detect Android devices if tool is available
    if requirements['android']:
        android_devices = detect_android_devices()
        devices.extend(android_devices)
        logger.info(f"Found {len(android_devices)} Android device(s)")
    else:
        logger.info("ADB not available - skipping Android detection")
    
    logger.info(f"Total devices found: {len(devices)}")
    
    return {
        'success': True,
        'devices': devices,
        'requirements': requirements,
        'output': f"Found {len(devices)} device(s) total"
    } 