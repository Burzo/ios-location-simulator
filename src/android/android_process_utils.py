import subprocess
import os
from src.config import setup_logging

logger = setup_logging()

def run_adb_command(command, timeout=30):
    """Execute ADB command and return result"""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(process.pid), 9)
            else:
                process.kill()
            stdout, stderr = process.communicate()
            return {
                'success': False,
                'output': stdout,
                'error': 'Command timeout'
            }
        
        # ADB-specific error pattern detection
        output_text = stdout + stderr
        error_patterns = [
            'device not found',
            'no devices/emulators found',
            'device offline',
            'device unauthorized',
            'permission denied',
            'failed to connect',
            'adb: not found'
        ]
        
        success_patterns = [
            'Success',
            'device',  # for device listing
            'mockLocation'  # for location commands
        ]
        
        has_error = any(pattern.lower() in output_text.lower() for pattern in error_patterns)
        has_success_indicator = any(pattern.lower() in output_text.lower() for pattern in success_patterns)
        
        # ADB command is successful if return code is 0 and no error patterns
        # Some ADB commands may have empty output but still be successful
        success = process.returncode == 0 and not has_error
        
        return {
            'success': success,
            'output': stdout,
            'error': stderr if stderr else (output_text if has_error else '')
        }
        
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

def check_adb_available():
    """Check if ADB is available and accessible"""
    result = run_adb_command('adb version', timeout=10)
    return result['success']

def get_device_property(device_id, property_name):
    """Get a specific property from an Android device"""
    command = f'adb -s {device_id} shell getprop {property_name}'
    result = run_adb_command(command)
    if result['success']:
        return result['output'].strip()
    return None 