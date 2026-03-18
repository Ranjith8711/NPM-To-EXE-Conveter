# Developer Documentation — NPM to EXE Converter

## Architecture Deep Dive

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  USER LAYER                                                      │
│  build.bat / build.sh / python build.py /path                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  PYTHON AUTOMATION LAYER  (python-automation/build.py)          │
│  • Prerequisites check    • Project validation                   │
│  • Dependency install     • Build execution                      │
│  • Runtime preparation    • EXE packaging                        │
│  • Output verification    • Error handling + retry               │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴─────────────────┐
        │                                  │
┌───────▼────────┐              ┌──────────▼──────────┐
│  CONVERTER     │              │  ELECTRON RUNTIME   │
│  ENGINE        │              │                     │
│  analyzer.js   │              │  main.js            │
│  optimizer.js  │              │  preload.js         │
└────────────────┘              └──────────┬──────────┘
                                           │
                                ┌──────────▼──────────┐
                                │  WEB APPLICATION    │
                                │  (your project)     │
                                │  webapp/            │
                                └─────────────────────┘
                                           │
                                ┌──────────▼──────────┐
                                │  ELECTRON-BUILDER   │
                                │  NSIS + portable    │
                                │  → output/*.exe     │
                                └─────────────────────┘
```

### Security Model

```
┌──────────────────────────────────────────────────────┐
│  Main Process (Node.js / full privileges)            │
│  • Window management                                 │
│  • File system access                               │
│  • Native dialogs                                   │
│  • Clipboard                                        │
│  • IPC handling                                     │
└───────────────────┬──────────────────────────────────┘
                    │  ipcMain.handle (secure typed API)
                    │  contextBridge.exposeInMainWorld
┌───────────────────▼──────────────────────────────────┐
│  Preload Script (isolated context)                   │
│  • contextBridge only                               │
│  • Typed API surface                                │
│  • Input validation                                 │
└───────────────────┬──────────────────────────────────┘
                    │  window.desktopAPI (typed interface)
┌───────────────────▼──────────────────────────────────┐
│  Renderer Process (web sandbox)                      │
│  nodeIntegration: false                             │
│  contextIsolation: true                             │
│  • No direct Node.js access                         │
│  • Full web API access                              │
│  • window.desktopAPI only for native ops            │
└──────────────────────────────────────────────────────┘
```

---

## Extending the Converter

### Adding a New Framework

1. Open `converter-engine/analyzer.js`
2. Add detection in `frameworkMap`:
```js
[['astro'], 'astro'],
[['remix'], 'remix'],
```
3. Add any special handling in `validateConfig()` if needed

### Adding a New Build Script Candidate

In `python-automation/build.py`, find `build_script_candidates`:
```python
for candidate in ["build", "build:prod", "dist", "compile", "generate", "export"]:
```

### Custom Electron Window Settings

Edit `electron-runtime/src/main.js` in the `createWindow()` function.
The Python layer can also inject values via the package.json `build.win` config.

### Adding IPC Handlers

In `electron-runtime/src/main.js`:
```js
ipcMain.handle('my-feature:do-thing', async (event, arg) => {
  // do native operation
  return { ok: true, result: ... };
});
```

In `electron-runtime/preload/preload.js`:
```js
contextBridge.exposeInMainWorld('desktopAPI', {
  // ... existing ...
  myFeature: {
    doThing: (arg) => ipcRenderer.invoke('my-feature:do-thing', arg),
  }
});
```

### Adding Linux / macOS Targets

The `electron-runtime/package.json` already has Linux and Mac targets configured.
To build for them, modify the Python build command:
```python
# For Linux:
"npx electron-builder --linux --x64"

# For macOS (requires macOS build machine):
"npx electron-builder --mac"
```

---

## Python Build Script Reference

### Command Line Usage

```bash
# Use default input-project/ folder
python python-automation/build.py

# Specify custom project path
python python-automation/build.py /path/to/project

# Windows
python python-automation\build.py C:\Users\user\myapp
```

### Environment Variables

| Variable               | Default  | Effect                                        |
|------------------------|----------|-----------------------------------------------|
| `NODE_ENV`             | production | Passed to npm build                        |
| `GENERATE_SOURCEMAP`   | false    | Disables CRA source maps                      |
| `ELECTRON_MIRROR`      | npmmirror | Electron download mirror for reliability    |
| `CSC_IDENTITY_AUTO_DISCOVERY` | false | Skips macOS code signing                 |

### Retry Configuration

```python
MAX_RETRIES = 3  # Number of retry attempts for failed commands
```

### Log Files

All log files are written to `logs/` with timestamps:
- `npm-install_YYYYMMDD_HHMMSS.log`
- `npm-build_YYYYMMDD_HHMMSS.log`
- `electron-install_YYYYMMDD_HHMMSS.log`
- `electron-builder_YYYYMMDD_HHMMSS.log`

---

## Production Considerations

### Code Signing (Windows)

For production distribution, sign your EXE with a Windows code signing certificate:

1. Obtain a certificate (EV or OV) from DigiCert, Sectigo, etc.
2. Install it on your build machine
3. Set environment variables:
```bash
set CSC_LINK=path/to/certificate.pfx
set CSC_KEY_PASSWORD=your-password
```
4. Remove `CSC_IDENTITY_AUTO_DISCOVERY=false` from the Python script

### Auto-Update

Add electron-updater for automatic updates:
```bash
npm install electron-updater
```
Configure a release server (GitHub Releases, S3, etc.) in `electron-runtime/package.json`:
```json
"publish": {
  "provider": "github",
  "owner": "your-org",
  "repo": "your-app"
}
```

### Reducing EXE Size

- Use `compression: "maximum"` in electron-builder config (already set)
- Consider `electron-packager` with pruned node_modules
- Use `files` array to exclude unnecessary files
- For very small apps, consider `neutralinojs` or `tauri` as alternatives

---

## Troubleshooting Deep Dive

### Issue: `spawn ENOENT` during packaging

**Cause:** electron-builder can't find system tools (NSIS on Windows)
**Fix:** electron-builder installs NSIS automatically on Windows. On Linux, install via:
```bash
sudo apt-get install nsis
```

### Issue: App loads blank/white screen

**Cause:** `index.html` path resolution fails inside ASAR
**Fix:** Check `getWebappPath()` in `main.js` — add your build output dir to the candidates list

### Issue: `require is not defined` in renderer

**Cause:** nodeIntegration is correctly disabled — this is expected
**Fix:** Use `window.desktopAPI` for all native operations via the preload bridge

### Issue: `localStorage` data not persisting

**Cause:** `userData` path varies — but localStorage *does* persist in Electron by default
**Fix:** Verify you're not clearing it on startup. Data is stored in `%APPDATA%/appname/`

### Issue: Large EXE size (>150 MB)

**Cause:** Electron itself is ~90-120 MB. This is expected.
**Fix:** This is normal for Electron apps. Users download the Chromium engine once.
For smaller binaries, evaluate Tauri (uses system WebView) as an alternative.

---

## Credits

**Developed By Ranjith R**  

Architecture inspired by: Electron Builder, Tauri, NW.js, Neutralinojs
