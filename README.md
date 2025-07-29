# Multi-Platform Location Simulator

A web application that simulates GPS locations on both iOS and Android devices for testing location-based features.

## Supported Platforms

### iOS Support

- Uses **pymobiledevice3** for iOS device communication
- Supports iOS 17+ with RSD tunnel connections
- Fallback support for older iOS versions

### Android Support

- Uses **ADB (Android Debug Bridge)** for Android device communication
- Supports Android devices with USB debugging enabled
- Multiple location setting methods for maximum compatibility

## Features

### Universal Features

- **Multi-platform device detection** - Automatically detects both iOS and Android devices
- **Unified web interface** - Same interface works for both platforms
- **Custom GPS coordinates** - Set any latitude/longitude coordinates
- **Quick location buttons** - Major cities preset for easy testing

### iOS-Specific Features

- Connect via USB (required first) or WiFi network (after USB trust)
- Automatic Developer Mode activation
- DeveloperDiskImage mounting
- RSD tunnel support for iOS 18.x

### Android-Specific Features

- USB debugging and Developer Options validation
- Mock location permission setup
- Multiple location injection methods (broadcast, service calls, settings)
- Device property inspection

## Prerequisites

### Universal Requirements

1. **Docker and Docker Compose** - Required to run the application

### iOS Device Setup

2. **iOS Device Requirements**:
   - **USB**: Connect device and trust computer when prompted (required first)
   - **Network**: After USB trust established, device can be used over same WiFi network
   - Developer Mode enabled (app will attempt to enable automatically)
   - Device must be unlocked during setup

### Android Device Setup

2. **Android Device Requirements**:
   - **USB Debugging enabled** in Developer Options
   - **Developer Options enabled** in Settings
   - **Mock Location app** configured (app will attempt to configure automatically)
   - Device authorized for debugging when prompted

## Setup

1. **Install Docker**

   - macOS: Install Docker Desktop
   - Linux: Install docker and docker-compose
   - Windows: Install Docker Desktop with WSL2

2. **Run the application**

   ```bash
   git clone https://github.com/Burzo/ios-location-simulator
   cd ios-location-simulator
   docker compose up -d
   ```

3. **Access the interface**
   ```
   http://localhost:8080
   ```

## Usage

### Device Connection

1. **Check Devices**

   - Click "Check Devices" to scan for connected devices
   - Both iOS and Android devices will be detected automatically
   - Device cards will show platform type (iOS/Android) and device info

2. **Connect Device**
   - Click on a device card to connect and setup location services
   - **iOS**: Waits for Developer Mode setup, DiskImage mounting, and tunnel establishment
   - **Android**: Validates USB debugging, enables mock location permissions

### Location Simulation

1. **Set Custom Location**

   - Enter latitude/longitude coordinates in the input fields
   - Click "Set Location" to apply coordinates to the connected device

2. **Use Quick Locations**

   - Click preset city buttons for major locations worldwide
   - Instantly applies coordinates without manual entry

3. **Clear Location**
   - Click "Clear Location" to stop location simulation
   - Returns device to normal GPS behavior

## Platform-Specific Requirements

### iOS Requirements

- iOS device with Developer Mode enabled (app enables automatically)
- Device must be unlocked during setup
- **Connection**: USB cable required for initial trust, then WiFi network optional
- **Compatibility**: Supports iOS 17+ with RSD tunnel connections

### Android Requirements

- Android device with USB Debugging enabled
- Developer Options must be enabled in Settings
- Mock Location app configured (app attempts automatic setup)
- **Connection**: USB cable required for ADB connection
- **Compatibility**: Works with most Android versions supporting ADB

## Technical Details

### iOS Implementation

- Built on [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) for iOS device communication
- Uses RSD tunnels for iOS 18.x location simulation
- Fallback methods for older iOS versions
- Device-specific UDID targeting

### Android Implementation

- Built on Android Debug Bridge (ADB) for device communication
- Multiple location injection methods:
  - Activity Manager broadcasts
  - Mock location providers
  - System service calls
  - Settings modification
- Automatic mock location permission configuration

### Architecture

- **Platform Detection**: Automatically detects device types
- **Unified API**: Same REST endpoints work for both platforms
- **Platform Abstraction**: Clean separation of iOS and Android logic
- **Error Handling**: Platform-specific error messages and troubleshooting

## API Endpoints

- `GET /api/devices` - List connected devices (both platforms)
- `POST /api/connect` - Setup device connection (platform-aware)
- `POST /api/location/set` - Set GPS coordinates (platform-aware)
- `POST /api/location/clear` - Clear simulated location (platform-aware)
- `POST /api/disconnect` - Disconnect and cleanup (all platforms)
- `GET /api/status` - Platform status and diagnostics

## Troubleshooting

### iOS Issues

#### Device Not Found

- Ensure device is connected via USB and unlocked
- Make sure you've trusted the computer on your iOS device

#### Developer Mode Issues

- **App activation**: The app should automatically turn on Developer Mode during device setup
- **First-time activation issue**: If this is the first time Developer Mode is activated on your device, the toggle may appear off even after the app enables it
- **Solutions**:
  - Try connecting to the device twice in the app
  - Or manually enable it: Go to **Settings → Privacy & Security → Developer Mode** and make sure it's toggled on
- **Verification**: Always check that Developer Mode shows as "On" in Settings before attempting device connection

### Android Issues

#### Device Not Found

- Enable USB Debugging in Developer Options
- Authorize the computer when prompted on device
- Try running `adb devices` in terminal to verify connection

#### Mock Location Issues

- Enable Developer Options in Settings
- Set a Mock Location app in Developer Options
- Grant location permissions to the mock location app
- Some devices require manual mock location app selection

#### Permission Denied

- Ensure USB debugging is authorized
- Check that Developer Options are enabled
- Some features may require root access on older Android versions

### General Issues

#### Platform Tools Missing

- **iOS**: Install pymobiledevice3: `pip install pymobiledevice3`
- **Android**: Install Android SDK platform-tools and ensure `adb` is in PATH
- Docker environment includes both tools by default

#### Connection Timeout

- **iOS**: Try restarting the device and reconnecting
- **Android**: Restart ADB server: `adb kill-server && adb start-server`
- Check USB cable and try different USB ports
