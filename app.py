from flask import Flask, render_template, request, jsonify
from src.config import setup_logging
from src.device_manager import list_devices, connect_device, cleanup_existing_connections
from src.location_service import set_location, clear_location
from src.process_utils import run_pymobiledevice3_command

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
    """API endpoint to list connected iOS devices"""
    result = list_devices()
    return jsonify(result)

@app.route('/api/connect', methods=['POST'])
def api_connect_device():
    """API endpoint to connect and setup device for location testing"""
    data = request.get_json() if request.is_json else {}
    device_id = data.get('deviceId', None)
    
    result = connect_device(device_id)
    return jsonify(result)

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect_device():
    """API endpoint to disconnect current device and clean up connections"""
    cleanup_existing_connections()
    
    return jsonify({
        'success': True,
        'message': 'Device disconnected and connections cleaned up'
    })

@app.route('/api/location/set', methods=['POST'])
def api_set_location():
    """API endpoint to set device location to specified coordinates"""
    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    if not lat or not lng:
        return jsonify({
            'success': False,
            'message': 'Latitude and longitude are required'
        })
    
    result = set_location(lat, lng)
    return jsonify(result)

@app.route('/api/location/clear', methods=['POST'])
def api_clear_location():
    """API endpoint to clear simulated location"""
    result = clear_location()
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def api_get_status():
    """API endpoint to get device status and diagnostic information"""
    device_info = run_pymobiledevice3_command('python3 -m pymobiledevice3 usbmux list')
    mount_status = run_pymobiledevice3_command('python3 -m pymobiledevice3 mounter list')
    location_test = run_pymobiledevice3_command('python3 -m pymobiledevice3 developer dvt simulate-location set -- 37.7749 -122.4194')
    
    return jsonify({
        'devices': device_info['output'] if device_info['success'] else 'No devices found',
        'device_error': device_info['error'] if not device_info['success'] else None,
        'mounted_images': mount_status['output'] if mount_status['success'] else 'None',
        'location_service_test': 'Available' if location_test['success'] else 'Unavailable',
        'location_error': location_test['error'] if not location_test['success'] else None
    })

@app.route('/api/start-tunnel', methods=['POST'])
def api_start_tunnel():
    """API endpoint for manual tunnel start (debugging)"""
    result = run_pymobiledevice3_command('timeout 5 python3 -m pymobiledevice3 lockdown start-tunnel')
    
    return jsonify({
        'success': result['success'],
        'message': 'Tunnel start attempted',
        'output': result['output'],
        'error': result['error']
    })

if __name__ == '__main__':
    logger.info("Starting iOS Location Simulator server...")
    app.run(host='0.0.0.0', port=5000, debug=True) 