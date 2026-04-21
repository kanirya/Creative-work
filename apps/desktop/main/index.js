const { app, BrowserWindow, ipcMain } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const isDev = !app.isPackaged;
const DEV_SERVER_PORT = 3002;
const DEV_SERVER_URL = `http://localhost:${DEV_SERVER_PORT}`;

let mainWindow;

async function waitForServer(url, maxAttempts = 30) {
  const http = require('http');
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await new Promise((resolve, reject) => {
        http.get(url, (res) => resolve()).on('error', reject);
      });
      return true;
    } catch (e) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  return false;
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  let url;
  if (isDev) {
    const serverReady = await waitForServer(DEV_SERVER_URL);
    if (serverReady) {
      url = DEV_SERVER_URL;
      console.log(`Found Next.js dev server on port ${DEV_SERVER_PORT}`);
    } else {
      console.error(`Could not find Next.js dev server on port ${DEV_SERVER_PORT}`);
      url = DEV_SERVER_URL;
    }
  } else {
    url = `file://${path.join(__dirname, '../out/index.html')}`;
  }

  mainWindow.loadURL(url);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Check for updates
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for offline functionality
ipcMain.handle('get-offline-data', async (event, key) => {
  const Store = require('electron-store');
  const store = new Store();
  return store.get(key);
});

ipcMain.handle('set-offline-data', async (event, key, value) => {
  const Store = require('electron-store');
  const store = new Store();
  store.set(key, value);
  return true;
});

ipcMain.handle('clear-offline-data', async () => {
  const Store = require('electron-store');
  const store = new Store();
  store.clear();
  return true;
});

ipcMain.handle('check-network-status', async () => {
  return !require('dns').lookup('google.com', (err) => {
    return !err;
  });
});

// Auto-updater events
autoUpdater.on('update-available', () => {
  mainWindow.webContents.send('update-available');
});

autoUpdater.on('update-downloaded', () => {
  mainWindow.webContents.send('update-downloaded');
});

ipcMain.handle('install-update', () => {
  autoUpdater.quitAndInstall();
});
