'use strict';
/**
 * Electron Preload Script
 * Secure IPC bridge between renderer and main process
 * Context-isolated — no direct Node.js access in renderer
 * Developed By Ranjith R
 */

const { contextBridge, ipcRenderer } = require('electron');

// ─────────────────────────────────────────────
//  Expose secure desktop API to renderer
// ─────────────────────────────────────────────
contextBridge.exposeInMainWorld('desktopAPI', {

  /**
   * App information
   */
  getAppInfo: () => ipcRenderer.invoke('app:info'),

  /**
   * Open an external URL in the system browser
   * @param {string} url
   */
  openExternal: (url) => ipcRenderer.invoke('app:open-url', url),

  /**
   * Clipboard operations
   */
  clipboard: {
    write: (text) => ipcRenderer.invoke('clipboard:write', text),
    read:  ()     => ipcRenderer.invoke('clipboard:read'),
  },

  /**
   * Native file dialogs
   */
  dialog: {
    openFile: (options) => ipcRenderer.invoke('dialog:open-file', options),
    saveFile: (options) => ipcRenderer.invoke('dialog:save-file', options),
  },

  /**
   * Window controls
   */
  window: {
    fullscreen: (flag) => ipcRenderer.invoke('window:fullscreen', flag),
    minimize:   ()     => ipcRenderer.invoke('window:minimize'),
    maximize:   ()     => ipcRenderer.invoke('window:maximize'),
  },

  /**
   * Listen to main-process events
   * @param {string} channel
   * @param {Function} callback
   */
  on: (channel, callback) => {
    const allowed = ['update-available', 'app-ready', 'theme-change'];
    if (allowed.includes(channel)) {
      ipcRenderer.on(channel, (_, ...args) => callback(...args));
    }
  },

  /**
   * Detect desktop environment
   */
  isDesktop: true,
  platform:  process.platform,
  arch:      process.arch,
});

// ─────────────────────────────────────────────
//  DOMContentLoaded enhancements
// ─────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {

  // Add desktop class for CSS targeting
  document.documentElement.classList.add('electron-desktop');
  document.documentElement.setAttribute('data-platform', process.platform);

  // Intercept anchor clicks for external links
  document.addEventListener('click', (e) => {
    const anchor = e.target.closest('a[href]');
    if (!anchor) return;
    const href = anchor.getAttribute('href');
    if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
      e.preventDefault();
      ipcRenderer.invoke('app:open-url', href);
    }
  });

  // Disable right-click default context menu on non-input elements
  // (allows right-click on inputs/textareas for native paste)
  document.addEventListener('contextmenu', (e) => {
    const tag = e.target.tagName.toLowerCase();
    if (!['input', 'textarea', 'select'].includes(tag)) {
      // Allow devtools shortcut — don't prevent default in dev
    }
  });
});
