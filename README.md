# iOS Location Simulator

A web application that uses pymobiledevice3 to simulate GPS locations on iOS devices for testing location-based features.

## Features

- Connect to iOS devices via USB (required first) or WiFi network (after USB trust)
- Set custom GPS coordinates

## Prerequisites

1. **Docker and Docker Compose** - Required to run the application
2. **iOS Device Setup**:
   - **USB**: Connect device and trust computer when prompted (required first)
   - **Network**: After USB trust established, device can be used over same WiFi network

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

1. **Connect Device**

   - Click "Check Devices" to scan for connected iOS devices
   - Click on a device card to connect and setup location services
   - Wait for setup completion message

2. **Simulate Location**
   - Enter custom latitude/longitude coordinates
   - Or use quick location buttons for major cities

## Device Requirements

- iOS device with Developer Mode enabled
- Device must be unlocked during setup
- **Connection**: USB cable required for initial trust, then WiFi network optional

## Technical Details

- Supports iOS 17+ with RSD tunnel connections
- Fallback support for older iOS versions
- Device-specific UDID targeting

## API

- `GET /api/devices` - List connected devices
- `POST /api/connect` - Setup device connection
- `POST /api/location/set` - Set GPS coordinates
- `POST /api/disconnect` - Disconnect and cleanup

Built on [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) for iOS device communication.
