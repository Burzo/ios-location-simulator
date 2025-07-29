"""
Shared process utilities for cross-platform operations.
Platform-specific utilities are now in their respective modules:
- iOS: src/ios/ios_process_utils.py  
- Android: src/android/android_process_utils.py
"""

import subprocess
import os
from src.config import setup_logging

logger = setup_logging()

def run_command(command, timeout=30, platform_agnostic=True):
    """
    Execute a generic command and return result.
    This is a platform-agnostic version for shared operations.
    For platform-specific commands, use the appropriate platform modules.
    """
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
        
        return {
            'success': process.returncode == 0,
            'output': stdout,
            'error': stderr
        }
        
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

def check_command_available(command):
    """Check if a command is available in the system PATH"""
    try:
        result = subprocess.run(
            f"which {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def kill_process_by_name(process_name):
    """Kill processes by name (cross-platform)"""
    try:
        if os.name == 'nt':  # Windows
            command = f"taskkill /F /IM {process_name}"
        else:  # Unix-like
            command = f"pkill -f {process_name}"
        
        result = run_command(command)
        return result['success']
    except Exception as e:
        logger.warning(f"Failed to kill process {process_name}: {e}")
        return False 