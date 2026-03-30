/**
 * Preload — Secure contextBridge IPC
 * Exposes window.desktopAPI to the renderer.
 * BEST TEAM
 */

const { contextBridge, ipcRenderer } = require('electron');

const invoke = (channel, ...args) => ipcRenderer.invoke(channel, ...args);

contextBridge.exposeInMainWorld('desktopAPI', {
  isDesktop: true,

  getAppInfo:  ()         => invoke('app:info'),
  openExternal:(url)      => invoke('shell:openExternal', url),

  clipboard: {
    write: (text) => invoke('clipboard:write', text),
    read:  ()     => invoke('clipboard:read'),
  },

  dialog: {
    openFile: (opts) => invoke('dialog:openFile', opts),
    saveFile: (opts) => invoke('dialog:saveFile', opts),
  },

  window: {
    fullscreen: () => invoke('window:fullscreen'),
    minimize:   () => invoke('window:minimize'),
    maximize:   () => invoke('window:maximize'),
  },
});
