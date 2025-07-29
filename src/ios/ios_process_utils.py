import subprocess
import os
import time
import threading
from src.config import PROCESS_KILL_TIMEOUT, MONITOR_TIMEOUT, PROCESS_POLL_INTERVAL, DEFAULT_TUNNEL_TIMEOUT

def run_pymobiledevice3_command(command, timeout=30):
    """Execute pymobiledevice3 command and return result"""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Tunnel commands need special handling - they don't exit automatically
        if '--rsd' in command and 'simulate-location' in command:
            return _handle_tunnel_command(process)
        
        # Regular command execution
        return _handle_regular_command(process, timeout)
        
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

def _handle_tunnel_command(process):
    """Handle tunnel commands with SIGINT detection"""
    from src.config import setup_logging
    logger = setup_logging()
    
    logger.debug(f"Executing tunnel command")
    
    # Monitor output for SIGINT message in real-time
    ready_event = threading.Event()
    
    def monitor_output():
        """Monitor process output for SIGINT message"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < MONITOR_TIMEOUT:
                # Check if process ended
                if process.poll() is not None:
                    logger.debug("Process ended - stopping monitor")
                    break
                
                # Read from stdout
                try:
                    output = process.stdout.readline()
                    if output:
                        line = output.strip()
                        logger.debug(f"Process output: {line}")
                        if 'Press Ctrl+C to send a SIGINT' in line or 'SIGINT' in line:
                            logger.debug("Detected SIGINT message - process ready")
                            ready_event.set()
                            return
                    elif output == '':  # EOF reached
                        logger.debug("stdout EOF reached")
                        break
                except:
                    pass
                
                # Read from stderr  
                try:
                    error = process.stderr.readline()
                    if error:
                        line = error.strip()
                        logger.debug(f"Process error: {line}")
                        if 'Press Ctrl+C to send a SIGINT' in line or 'SIGINT' in line:
                            logger.debug("Detected SIGINT message - process ready")
                            ready_event.set()
                            return
                    elif error == '':  # EOF reached
                        logger.debug("stderr EOF reached")
                        break
                except:
                    pass
                    
                # Small delay to avoid busy waiting
                time.sleep(PROCESS_POLL_INTERVAL)
                
            logger.debug("Monitor timeout reached")
        except Exception as e:
            logger.debug(f"Output monitoring error: {e}")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_output, daemon=True)
    monitor_thread.start()
    
    # Wait for SIGINT message or timeout
    if ready_event.wait(timeout=DEFAULT_TUNNEL_TIMEOUT):
        logger.debug("Process ready - terminating")
    else:
        logger.debug("Timeout waiting for SIGINT - terminating anyway")
    
    return _terminate_process(process)

def _handle_regular_command(process, timeout):
    """Handle regular commands with standard timeout"""
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if hasattr(os, 'killpg'):
            os.killpg(os.getpgid(process.pid), 9)
        else:
            process.kill()
        stdout, stderr = process.communicate()
    
    # Error pattern detection
    output_text = stdout + stderr
    error_patterns = [
        'InvalidServiceError',
        'Unable to connect to Tunneld',
        'Cannot enable developer-mode when passcode is set',
        'DeveloperDiskImage not mounted',
        'No such file or directory'
    ]
    
    normal_patterns = [
        'Press Ctrl+C to send a SIGINT',
        'tunnel created',
        'Use the follow connection option'
    ]
    
    has_error = any(pattern in output_text for pattern in error_patterns)
    is_normal_output = any(pattern in output_text for pattern in normal_patterns)
    
    if is_normal_output:
        has_error = False
    
    return {
        'success': process.returncode == 0 and not has_error,
        'output': stdout,
        'error': stderr if stderr else (output_text if has_error else '')
    }

def _terminate_process(process):
    """Terminate a process gracefully with fallback to force kill"""
    from src.config import setup_logging
    logger = setup_logging()
    
    try:
        if hasattr(os, 'killpg'):
            os.killpg(os.getpgid(process.pid), 15)
        else:
            process.terminate()
        
        try:
            process.communicate(timeout=PROCESS_KILL_TIMEOUT)
        except subprocess.TimeoutExpired:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(process.pid), 9)
            else:
                process.kill()
            process.communicate()
        
        logger.debug("Process terminated successfully")
        return {
            'success': True,
            'output': 'Command executed successfully',
            'error': ''
        }
    except Exception as e:
        logger.warning(f"Error terminating process: {e}")
        return {
            'success': False,
            'output': '',
            'error': f'Process termination error: {e}'
        } 