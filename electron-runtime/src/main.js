'use strict';
/**
 * Electron Main Process
 * NPM → EXE Converter Runtime
 * Developed By Ranjith R
 */

const { app, BrowserWindow, shell, ipcMain, dialog, clipboard, Menu, screen } = require('electron');
const path  = require('path');
const fs    = require('fs');
const url   = require('url');

// ─────────────────────────────────────────────
//  App metadata (injected by Python build)
// ─────────────────────────────────────────────
const APP_NAME    = '__APP_NAME__';
const APP_VERSION = '__APP_VERSION__';

// ─────────────────────────────────────────────
//  Security: disable hardware-based exploits
// ─────────────────────────────────────────────
app.commandLine.appendSwitch('disable-features', 'OutOfBlinkCors');
app.commandLine.appendSwitch('enable-gpu-rasterization');
app.commandLine.appendSwitch('enable-zero-copy');
app.commandLine.appendSwitch('ignore-certificate-errors');

// ─────────────────────────────────────────────
//  Window management
// ─────────────────────────────────────────────
let mainWindow = null;

function getWebappPath() {
  // In packaged app: <resources>/app.asar/webapp/
  // In dev:          <project-root>/webapp/
  const candidates = [
    path.join(__dirname, '..', 'webapp'),
    path.join(process.resourcesPath || '', 'app.asar', 'webapp'),
    path.join(process.resourcesPath || '', 'webapp'),
    path.join(app.getAppPath(), 'webapp'),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return path.join(__dirname, '..', 'webapp');
}

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width:           Math.min(1280, width),
    height:          Math.min(800,  height),
    minWidth:        800,
    minHeight:       600,
    title:           APP_NAME,
    backgroundColor: '#0a0a0f',
    show:            false,   // prevent flash
    frame:           true,
    autoHideMenuBar: false,
    webPreferences: {
      preload:               path.join(__dirname, '..', 'preload', 'preload.js'),
      contextIsolation:      true,
      nodeIntegration:       false,   // SECURITY: disabled
      nodeIntegrationInWorker: false,
      sandbox:               false,   // Allow preload
      webSecurity:           true,
      allowRunningInsecureContent: false,
      enableBlinkFeatures:   '',
      webviewTag:            false,
      plugins:               false,
      experimentalFeatures:  false,
    }
  });

  // ── Menu bar ──────────────────────────────
  buildMenu();

  // ── Load the webapp ───────────────────────
  const webappPath = getWebappPath();
  const indexFile  = findIndexFile(webappPath);

  if (indexFile) {
    const fileUrl = url.pathToFileURL(indexFile).toString();
    mainWindow.loadURL(fileUrl);
  } else {
    mainWindow.loadURL(`data:text/html,<h1 style="font-family:sans-serif;color:#fff;background:#111;height:100vh;margin:0;display:grid;place-items:center">No index.html found in webapp/</h1>`);
  }

  // ── Show once ready ───────────────────────
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  // ── Handle external links ─────────────────
  mainWindow.webContents.setWindowOpenHandler(({ url: targetUrl }) => {
    if (isExternalUrl(targetUrl)) {
      shell.openExternal(targetUrl);
    }
    return { action: 'deny' };
  });

  // Override navigation for external links
  mainWindow.webContents.on('will-navigate', (event, navUrl) => {
    const appUrl = mainWindow.webContents.getURL();
    if (isExternalUrl(navUrl) && navUrl !== appUrl) {
      event.preventDefault();
      shell.openExternal(navUrl);
    }
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

function findIndexFile(webappDir) {
  const candidates = ['index.html', 'index.htm', 'public/index.html', 'dist/index.html'];
  for (const rel of candidates) {
    const full = path.join(webappDir, rel);
    if (fs.existsSync(full)) return full;
  }
  // Recursive search (one level)
  if (fs.existsSync(webappDir)) {
    const files = fs.readdirSync(webappDir);
    for (const f of files) {
      if (f === 'index.html' || f === 'index.htm') {
        return path.join(webappDir, f);
      }
    }
  }
  return null;
}

function isExternalUrl(target) {
  return target && (target.startsWith('http://') || target.startsWith('https://')) &&
    !target.startsWith('file://');
}

// ─────────────────────────────────────────────
//  Menu
// ─────────────────────────────────────────────
function buildMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        { label: 'Reload',        accelerator: 'CmdOrCtrl+R',  click: () => mainWindow?.webContents.reload() },
        { label: 'Force Reload',  accelerator: 'CmdOrCtrl+Shift+R', click: () => mainWindow?.webContents.reloadIgnoringCache() },
        { type: 'separator' },
        { label: 'Quit',          accelerator: 'Alt+F4',        role: 'quit' },
      ]
    },
    {
      label: 'View',
      submenu: [
        { label: 'Zoom In',       accelerator: 'CmdOrCtrl+=',  click: () => adjustZoom(0.1) },
        { label: 'Zoom Out',      accelerator: 'CmdOrCtrl+-',  click: () => adjustZoom(-0.1) },
        { label: 'Reset Zoom',    accelerator: 'CmdOrCtrl+0',  click: () => mainWindow?.webContents.setZoomLevel(0) },
        { type: 'separator' },
        { label: 'Toggle Fullscreen', accelerator: 'F11',      click: () => mainWindow?.setFullScreen(!mainWindow.isFullScreen()) },
      ]
    },
    {
      label: 'Tools',
      submenu: [
        { label: 'Dev Tools', accelerator: 'F12',
          click: () => mainWindow?.webContents.toggleDevTools() },
        { label: 'Copy URL',
          click: () => clipboard.writeText(mainWindow?.webContents.getURL() || '') },
      ]
    },
    {
      label: 'About',
      click: () => {
        dialog.showMessageBox(mainWindow, {
          type:    'info',
          title:   `About ${APP_NAME}`,
          message: `${APP_NAME} v${APP_VERSION}`,
          detail:  `Built with Electron\nNPM → EXE Converter\n\nDeveloped By Ranjith R,
          buttons: ['OK']
        });
      }
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function adjustZoom(delta) {
  if (!mainWindow) return;
  const current = mainWindow.webContents.getZoomLevel();
  mainWindow.webContents.setZoomLevel(current + delta);
}

// ─────────────────────────────────────────────
//  IPC Handlers (secure, context-isolated)
// ─────────────────────────────────────────────
ipcMain.handle('app:info', () => ({
  name:     APP_NAME,
  version:  APP_VERSION,
  platform: process.platform,
  arch:     process.arch,
}));

ipcMain.handle('app:open-url', (_, target) => {
  if (typeof target === 'string' && isExternalUrl(target)) {
    shell.openExternal(target);
    return { ok: true };
  }
  return { ok: false, error: 'Invalid URL' };
});

ipcMain.handle('clipboard:write', (_, text) => {
  clipboard.writeText(String(text));
  return { ok: true };
});

ipcMain.handle('clipboard:read', () => ({
  ok: true, text: clipboard.readText()
}));

ipcMain.handle('dialog:open-file', async (_, opts) => {
  const result = await dialog.showOpenDialog(mainWindow, opts || {});
  return result;
});

ipcMain.handle('dialog:save-file', async (_, opts) => {
  const result = await dialog.showSaveDialog(mainWindow, opts || {});
  return result;
});

ipcMain.handle('window:fullscreen', (_, flag) => {
  mainWindow?.setFullScreen(flag === undefined ? !mainWindow.isFullScreen() : flag);
});

ipcMain.handle('window:minimize', ()  => mainWindow?.minimize());
ipcMain.handle('window:maximize', ()  => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});

// ─────────────────────────────────────────────
//  App lifecycle
// ─────────────────────────────────────────────
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Prevent multiple instances
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// Security: prevent new webviews
app.on('web-contents-created', (_, contents) => {
  contents.on('will-attach-webview', (event) => {
    event.preventDefault();
  });
});
