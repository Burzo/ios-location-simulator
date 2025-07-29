from flask import Flask, render_template, request, jsonify
from src.config import setup_logging
from src.device_manager import list_devices, connect_device, cleanup_existing_connections
from src.location_service import set_location, clear_location
from src.platform_detector import check_platform_requirements
from src.ios.ios_process_utils import run_pymobiledevice3_command

# Setup logging
logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/devices', methods=['GET'])
def api_list_devices():
    """API endpoint to list connected devices across all platforms"""
    result = list_devices()
    return jsonify(result)

@app.route('/api/connect', methods=['POST'])
def api_connect_device():
    """API endpoint to connect and setup device for location testing"""
    data = request.get_json() if request.is_json else {}
    device_id = data.get('deviceId', None)
    platform = data.get('platform', None)  # Now support platform parameter
    
    result = connect_device(device_id, platform)
    return jsonify(result)

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect_device():
    """API endpoint to disconnect current device and clean up connections"""
    cleanup_existing_connections()
    
    return jsonify({
        'success': True,
        'message': 'All devices disconnected and connections cleaned up'
    })

@app.route('/api/location/set', methods=['POST'])
def api_set_location():
    """API endpoint to set device location to specified coordinates"""
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')
    device_id = data.get('deviceId', None)  # Optional device ID
    platform = data.get('platform', None)  # Optional platform
    
    if not lat or not lng:
        return jsonify({
            'success': False,
            'message': 'Latitude and longitude are required'
        })
    
    result = set_location(lat, lng, device_id, platform)
    return jsonify(result)

@app.route('/api/location/clear', methods=['POST'])
def api_clear_location():
    """API endpoint to clear simulated location"""
    data = request.get_json() if request.is_json else {}
    device_id = data.get('deviceId', None)  # Optional device ID
    platform = data.get('platform', None)  # Optional platform
    
    result = clear_location(device_id, platform)
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def api_get_status():
    """API endpoint to get platform status and diagnostic information"""
    # Check platform requirements
    requirements = check_platform_requirements()
    
    status = {
        'platforms': requirements,
        'devices': {},
        'services': {}
    }
    
    # iOS diagnostics (if available)
    if requirements.get('ios', False):
        try:
            device_info = run_pymobiledevice3_command('python3 -m pymobiledevice3 usbmux list')
            mount_status = run_pymobiledevice3_command('python3 -m pymobiledevice3 mounter list')
            location_test = run_pymobiledevice3_command('python3 -m pymobiledevice3 developer dvt simulate-location set -- 37.7749 -122.4194')
            
            status['devices']['ios'] = device_info['output'] if device_info['success'] else 'No iOS devices found'
            status['services']['ios'] = {
                'device_error': device_info['error'] if not device_info['success'] else None,
                'mounted_images': mount_status['output'] if mount_status['success'] else 'None',
                'location_service_test': 'Available' if location_test['success'] else 'Unavailable',
                'location_error': location_test['error'] if not location_test['success'] else None
            }
        except Exception as e:
            status['services']['ios'] = {'error': str(e)}
    
    # Android diagnostics (if available)
    if requirements.get('android', False):
        try:
            from src.android.android_process_utils import run_adb_command
            device_info = run_adb_command('adb devices -l')
            version_info = run_adb_command('adb version')
            
            status['devices']['android'] = device_info['output'] if device_info['success'] else 'No Android devices found'
            status['services']['android'] = {
                'adb_version': version_info['output'].split('\n')[0] if version_info['success'] else 'Unknown',
                'device_error': device_info['error'] if not device_info['success'] else None
            }
        except Exception as e:
            status['services']['android'] = {'error': str(e)}
    
    return jsonify(status)

@app.route('/api/start-tunnel', methods=['POST'])
def api_start_tunnel():
    """API endpoint for manual iOS tunnel start (debugging)"""
    data = request.get_json() if request.is_json else {}
    platform = data.get('platform', 'ios')
    
    if platform == 'ios':
        result = run_pymobiledevice3_command('timeout 5 python3 -m pymobiledevice3 lockdown start-tunnel')
        return jsonify({
            'success': result['success'],
            'message': 'iOS tunnel start attempted',
            'output': result['output'],
            'error': result['error']
        })
    elif platform == 'android':
        # Android doesn't need tunnels, but we can provide ADB server restart
        from src.android.android_process_utils import run_adb_command
        result = run_adb_command('adb kill-server && adb start-server')
        return jsonify({
            'success': result['success'],
            'message': 'ADB server restart attempted',
            'output': result['output'],
            'error': result['error']
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Platform {platform} not supported for tunnel operations'
        })

if __name__ == '__main__':
    logger.info("Starting Multi-Platform Location Simulator server...")
    logger.info("Supported platforms: iOS (pymobiledevice3), Android (ADB)")
    app.run(host='0.0.0.0', port=5000, debug=True) 