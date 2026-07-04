const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let pyProcess = null;

function startBackend() {
  console.log('Locating backend process...');
  const fs = require('fs');
  const isWin = process.platform === 'win32';
  const exeSuffix = isWin ? '.exe' : '';

  // Paths: dev build output or packaged alongside the Electron app
  const devBackendPath = path.join(__dirname, `../dist/eye_yantra_backend/eye_yantra_backend${exeSuffix}`);
  const packagedBackendPath = path.join(__dirname, `eye_yantra_backend/eye_yantra_backend${exeSuffix}`);

  let backendExe = null;

  if (fs.existsSync(devBackendPath)) {
    backendExe = devBackendPath;
  } else if (fs.existsSync(packagedBackendPath)) {
    backendExe = packagedBackendPath;
  }

  if (!backendExe) {
    console.log('Compiled backend binary not found, falling back to python script...');
    const pythonCmd = isWin ? 'python' : 'python3';
    const backendScript = path.join(__dirname, '../app_api.py');
    pyProcess = spawn(pythonCmd, [backendScript], {
      cwd: path.join(__dirname, '..'),
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      // On Windows, open a hidden console window for the Python process
      windowsHide: true
    });
  } else {
    console.log(`Starting compiled backend executable: ${backendExe}`);
    pyProcess = spawn(backendExe, [], {
      cwd: path.dirname(backendExe),
      env: { ...process.env },
      windowsHide: true
    });
  }

  pyProcess.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data}`);
  });

  pyProcess.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data}`);
  });

  pyProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

function checkServerReady(url, callback) {
  const interval = setInterval(() => {
    http.get(url, (res) => {
      // Check if server returns any response (usually redirect or HTML page)
      if (res.statusCode === 200 || res.statusCode === 302) {
        console.log('Flask backend is fully active and listening!');
        clearInterval(interval);
        callback();
      }
    }).on('error', () => {
      // Still booting up, keep polling...
    });
  }, 500);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "EyeYantra Ocular Alignment Workstation",
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      enableRemoteModule: false
    }
  });

  // Load the beautiful splash screen first
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));

  const flaskUrl = 'http://127.0.0.1:5000/';

  // Wait for backend to be ready, then redirect to Flask pages
  checkServerReady(flaskUrl, () => {
    if (mainWindow) {
      mainWindow.loadURL(flaskUrl);
    }
  });

  // Handle Web Bluetooth device selection
  mainWindow.webContents.on('select-bluetooth-device', (event, deviceList, callback) => {
    event.preventDefault();
    console.log('Bluetooth devices discovered:', deviceList);
    
    // Automatically select the EyeYantra Ameba BLE headset if present
    const amebaDevice = deviceList.find(d => d.deviceName.includes('AMEBA_BLE_DEV') || d.deviceName.includes('EyeYantra'));
    if (amebaDevice) {
      callback(amebaDevice.deviceId);
    } else if (deviceList.length > 0) {
      // Fallback to first device found
      callback(deviceList[0].deviceId);
    } else {
      console.log('No Bluetooth devices available to match.');
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers for Wi-Fi management (cross-platform: nmcli on Linux, netsh on Windows)
ipcMain.handle('scan-wifi', async () => {
  return new Promise((resolve) => {
    const { exec } = require('child_process');
    const isWin = process.platform === 'win32';

    if (isWin) {
      // Windows: use netsh to list Wi-Fi networks
      exec('netsh wlan show networks mode=Bssid', { encoding: 'utf8' }, (error, stdout) => {
        if (error) {
          console.error('Scan WiFi error (Windows):', error);
          return resolve([{ ssid: 'EyeYantra_AP', signal: 99 }]);
        }
        const networks = [];
        const seen = new Set();
        const ssidMatches = stdout.match(/SSID\s+\d+\s*:\s*(.+)/g) || [];
        const signalMatches = stdout.match(/Signal\s*:\s*(\d+)%/g) || [];
        ssidMatches.forEach((line, i) => {
          const ssid = line.replace(/SSID\s+\d+\s*:\s*/, '').trim();
          const signalStr = signalMatches[i] ? signalMatches[i].match(/(\d+)/)[1] : '50';
          if (ssid && !seen.has(ssid)) {
            seen.add(ssid);
            networks.push({ ssid, signal: parseInt(signalStr, 10) });
          }
        });
        resolve(networks);
      });
    } else {
      // Linux: use nmcli
      exec('nmcli -t -f SSID,SIGNAL dev wifi list', (error, stdout) => {
        if (error) {
          console.error('Scan WiFi error (Linux):', error);
          return resolve([
            { ssid: 'EyeYantra_AP', signal: 99 },
            { ssid: 'Hospital_Staff_5G', signal: 85 }
          ]);
        }
        const networks = [];
        const lines = stdout.split('\n');
        const seen = new Set();
        for (const line of lines) {
          if (!line.trim()) continue;
          const parts = line.split(':');
          if (parts.length >= 2) {
            const ssid = parts.slice(0, -1).join(':').trim();
            const signal = parseInt(parts[parts.length - 1], 10);
            if (ssid && !seen.has(ssid)) {
              seen.add(ssid);
              networks.push({ ssid, signal });
            }
          }
        }
        resolve(networks);
      });
    }
  });
});

ipcMain.handle('connect-wifi', async (event, { ssid, password }) => {
  return new Promise((resolve) => {
    const { exec } = require('child_process');
    const isWin = process.platform === 'win32';

    if (isWin) {
      // Windows: create a WLAN profile XML and connect via netsh
      const profileXml = `<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>${ssid}</name>
  <SSIDConfig><SSID><name>${ssid}</name></SSID></SSIDConfig>
  <connectionType>ESS</connectionType>
  <connectionMode>auto</connectionMode>
  <MSM><security>
    <authEncryption><authentication>WPA2PSK</authentication><encryption>AES</encryption></authEncryption>
    <sharedKey><keyType>passPhrase</keyType><protected>false</protected><keyMaterial>${password}</keyMaterial></sharedKey>
  </security></MSM>
</WLANProfile>`;
      const { writeFileSync, unlinkSync } = require('fs');
      const profilePath = path.join(require('os').tmpdir(), `eyeyantra_wifi_${Date.now()}.xml`);
      try {
        writeFileSync(profilePath, profileXml);
        exec(`netsh wlan add profile filename="${profilePath}" & netsh wlan connect name="${ssid}"`, (error, stdout, stderr) => {
          try { unlinkSync(profilePath); } catch (_) {}
          if (error) {
            console.error('Connect WiFi error (Windows):', error);
            return resolve({ success: false, message: stderr || error.message });
          }
          resolve({ success: true, message: `Connected to ${ssid}` });
        });
      } catch (e) {
        resolve({ success: false, message: e.message });
      }
    } else {
      // Linux: use nmcli
      const cmd = `nmcli dev wifi connect "${ssid.replace(/"/g, '\\"')}" password "${password.replace(/"/g, '\\"')}"`;
      exec(cmd, (error, stdout, stderr) => {
        if (error) {
          console.error('Connect WiFi error (Linux):', error);
          return resolve({ success: false, message: stderr || error.message });
        }
        resolve({ success: true, message: stdout });
      });
    }
  });
});

app.whenReady().then(() => {
  // Set chrome flags for Bluetooth
  app.commandLine.appendSwitch('enable-experimental-web-platform-features', 'true');
  app.commandLine.appendSwitch('enable-web-bluetooth', 'true');
  
  // Start backend process
  startBackend();

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Clean up processes on exit
function killBackend() {
  if (pyProcess) {
    console.log('Killing Python backend process...');
    try {
      if (process.platform === 'win32') {
        // On Windows, use taskkill to ensure all child processes are terminated
        const { execSync } = require('child_process');
        execSync(`taskkill /PID ${pyProcess.pid} /T /F`, { stdio: 'ignore' });
      } else {
        pyProcess.kill('SIGTERM');
      }
    } catch (e) {
      console.error('Error killing backend:', e.message);
    }
    pyProcess = null;
  }
}

app.on('window-all-closed', () => {
  killBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  killBackend();
});
