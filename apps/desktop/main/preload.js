const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  // Offline data management
  getOfflineData: (key) => ipcRenderer.invoke('get-offline-data', key),
  setOfflineData: (key, value) => ipcRenderer.invoke('set-offline-data', key, value),
  clearOfflineData: () => ipcRenderer.invoke('clear-offline-data'),
  
  // Network status
  checkNetworkStatus: () => ipcRenderer.invoke('check-network-status'),
  
  // Auto-updater
  onUpdateAvailable: (callback) => ipcRenderer.on('update-available', callback),
  onUpdateDownloaded: (callback) => ipcRenderer.on('update-downloaded', callback),
  installUpdate: () => ipcRenderer.invoke('install-update'),
});
