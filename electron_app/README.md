# EyeYantra Desktop App — Windows & Linux Setup Guide

This Electron wrapper packages the EyeYantra Flask backend into a native desktop application.
It works on **Windows 10/11** and **Ubuntu 20.04+**.

---

## Features

| Feature | Windows | Linux |
|---------|---------|-------|
| Auto-starts Python backend | ✅ | ✅ |
| BLE device auto-select | ✅ | ✅ |
| Wi-Fi scan & connect | ✅ (via `netsh`) | ✅ (via `nmcli`) |
| One-click installer | ✅ NSIS + Portable | ✅ AppImage + .deb |
| Kills backend on exit | ✅ `taskkill /T /F` | ✅ `SIGTERM` |

---

## Running for Development (Both Platforms)

### Prerequisites
- **Python 3.10+** in PATH
- **Node.js 18+** and **npm**

### Steps

```bash
# 1. Install Python backend deps
pip install -r requirements_windows.txt   # Windows
# or
pip3 install -r requirements_ubuntu.txt   # Linux

# 2. Install Electron dependencies
cd electron_app
npm install

# 3. Start Flask backend (in a separate terminal)
cd ..
python app_api.py          # Windows
# or
python3 app_api.py         # Linux

# 4. Launch the Electron shell
cd electron_app
npm start
```

---

## Building a Windows Installer

### Option A — One-Click Batch Script (Recommended)

On a **Windows machine**, double-click `build_windows.bat` in the project root.
It will:
1. Install Python dependencies
2. Run PyInstaller to build `eye_yantra_backend.exe`
3. Copy the binary into `electron_app/eye_yantra_backend/`
4. Run `electron-builder` to produce:
   - `electron_app/dist_installer/EyeYantra Setup <version>.exe` ← NSIS installer
   - `electron_app/dist_installer/EyeYantra <version>.exe` ← Portable executable

### Option B — Manual Steps

```bat
REM On Windows CMD / PowerShell
pip install pyinstaller
pyinstaller eye_yantra_backend_windows.spec --noconfirm --clean

xcopy /E /I dist\eye_yantra_backend electron_app\eye_yantra_backend

cd electron_app
npm install
npm run build-win
```

---

## Building a Linux Package

```bash
cd electron_app
npm install
npm run build-linux
# Output: dist_installer/EyeYantra-<version>.AppImage
#         dist_installer/eyeyantra_<version>_amd64.deb
```

---

## Project Structure

```
EYE_YENTRA_Code/
├── app_api.py                         # Flask backend (main entry point)
├── eye_yantra_backend.spec            # PyInstaller spec (Linux)
├── eye_yantra_backend_windows.spec    # PyInstaller spec (Windows)
├── build_windows.bat                  # One-click Windows build script
├── requirements_windows.txt
├── requirements_ubuntu.txt
└── electron_app/
    ├── main.js          # Electron main process (cross-platform)
    ├── preload.js       # Context bridge for renderer
    ├── loading.html     # Splash screen
    ├── package.json     # npm + electron-builder config
    └── eye_yantra_backend/   # Populated by build script
        └── eye_yantra_backend.exe  (Windows)
        └── eye_yantra_backend      (Linux)
```

---

## Frontend Integration

The Electron wrapper injects `window.electronAPI` into every Flask page:

```javascript
if (window.electronAPI && window.electronAPI.isElectron) {

  // Scan nearby Wi-Fi networks
  window.electronAPI.scanWifi().then(networks => {
    console.log('Networks:', networks); // [{ssid:'...', signal:85}, ...]
  });

  // Connect to a Wi-Fi network
  window.electronAPI.connectWifi('EyeYantra_AP', 'password123').then(res => {
    if (res.success) alert('Connected!');
    else alert('Failed: ' + res.message);
  });
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend doesn't start | Check Python is in `PATH`; run `python app_api.py` manually |
| Antivirus blocks `.exe` | Add `dist\eye_yantra_backend\` to AV exclusions |
| Webcam not detected | Run app as Administrator; check Device Manager |
| BLE not working | Enable Bluetooth in Windows settings; pair device first |
| Port 5000 in use | Kill the conflicting process: `netstat -ano \| findstr :5000` then `taskkill /PID <id> /F` |
