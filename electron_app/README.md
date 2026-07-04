# EyeYantra Desktop App Wrapper (Electron)

This wrapper packages the EyeYantra Flask web templates into a desktop application shell, providing access to Bluetooth Low Energy (BLE) and Wi-Fi networks on Ubuntu.

## Features

1. **Web Bluetooth Support**: Automatically handles BLE device authorization for `AMEBA_BLE_DEV`.
2. **Wi-Fi Integration**: Exposes safe APIs to scan and connect to local Wi-Fi networks on Linux (Ubuntu) using the system's `nmcli` CLI tool.

## Installation & Running

Ensure you have Node.js and npm installed on your Ubuntu machine.

1. **Install dependencies**:
   ```bash
   cd electron_app
   npm install
   ```

2. **Start the Flask Python backend**:
   ```bash
   python3 app_api.py
   ```

3. **Launch the Electron App**:
   ```bash
   npm start
   ```

## Frontend Integration

The Electron wrapper injects `window.electronAPI` into the frontend. You can use it in your templates/pages like this:

```javascript
if (window.electronAPI && window.electronAPI.isElectron) {
  console.log("Running inside Electron desktop wrapper.");
  
  // Scan local Wi-Fi networks
  window.electronAPI.scanWifi().then(networks => {
    console.log("Scanned networks:", networks);
  });

  // Connect to a Wi-Fi network
  window.electronAPI.connectWifi('SSID_Name', 'Password').then(res => {
    if (res.success) {
      alert("Connected successfully!");
    } else {
      alert("Connection failed: " + res.message);
    }
  });
}
```
