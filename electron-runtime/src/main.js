/**
 * Electron Main Process
 * NPM → EXE Converter — BEST TEAM
 */

const { app, BrowserWindow, ipcMain, shell, clipboard, dialog } = require('electron');
const path = require('path');
const url  = require('url');

const APP_NAME    = '__APP_NAME__';
const APP_VERSION = '__APP_VERSION__';

let mainWindow = null;

// ─── Window ───────────────────────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width:           1280,
    height:          800,
    minWidth:        800,
    minHeight:       600,
    title:           APP_NAME,
    show:            false,   // reveal after ready-to-show
    backgroundColor: '#1a1a2e',
    webPreferences: {
      preload:              path.join(__dirname, '..', 'preload', 'preload.js'),
      contextIsolation:     true,
      nodeIntegration:      false,
      sandbox:              false,
      webSecurity:          true,
    },
  });

  // Load bundled webapp
  const indexPath = path.join(__dirname, '..', 'webapp', 'index.html');
  mainWindow.loadURL(
    url.format({ pathname: indexPath, protocol: 'file:', slashes: true })
  );

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => { if (!mainWindow) createWindow(); });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// ─── IPC Handlers ─────────────────────────────────────────────────────────────

ipcMain.handle('app:info', () => ({
  name:     APP_NAME,
  version:  APP_VERSION,
  platform: process.platform,
  arch:     process.arch,
  isDesktop: true,
}));

ipcMain.handle('shell:openExternal', async (_e, rawUrl) => {
  try {
    const parsed = new URL(rawUrl);
    if (!['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
      throw new Error(`Blocked protocol: ${parsed.protocol}`);
    }
    await shell.openExternal(rawUrl);
    return { ok: true };
  } catch (ex) {
    return { ok: false, error: ex.message };
  }
});

ipcMain.handle('clipboard:write', (_e, text) => {
  clipboard.writeText(String(text));
  return { ok: true };
});

ipcMain.handle('clipboard:read', () => ({ ok: true, text: clipboard.readText() }));

ipcMain.handle('dialog:openFile', async (_e, opts = {}) => {
  const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    ...opts,
  });
  return { canceled, filePaths };
});

ipcMain.handle('dialog:saveFile', async (_e, opts = {}) => {
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, opts);
  return { canceled, filePath };
});

ipcMain.handle('window:fullscreen', () => {
  mainWindow.setFullScreen(!mainWindow.isFullScreen());
  return { ok: true };
});

ipcMain.handle('window:minimize', () => { mainWindow.minimize(); return { ok: true }; });
ipcMain.handle('window:maximize', () => {
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
  return { ok: true };
});
