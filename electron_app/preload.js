const { contextBridge, ipcRenderer } = require('electron');

// Expose safe APIs to the web app renderer process (Flask pages)
contextBridge.exposeInMainWorld('electronAPI', {
  // Wi-Fi APIs
  scanWifi: () => ipcRenderer.invoke('scan-wifi'),
  connectWifi: (ssid, password) => ipcRenderer.invoke('connect-wifi', { ssid, password }),
  
  // Platform flag
  isElectron: true
});
