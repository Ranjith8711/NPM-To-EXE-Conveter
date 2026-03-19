# NPM Project → Windows Desktop EXE Converter

**Production-grade tool to convert any NPM web project into a standalone Windows `.exe`**
   
> Developed By [Ranjith R]

---

## Overview

This tool wraps any modern NPM web application (React, Vue, Vite, Webpack, Vanilla, etc.) inside an Electron desktop runtime and packages it as a self-contained Windows executable. The final `.exe` runs **without requiring Node.js or any external dependencies** on the user's machine.

---

## System Requirements

| Tool     | Minimum Version | Install                         |
|----------|----------------|---------------------------------|
| Python   | 3.8+           | https://python.org              |
| Node.js  | 16.x+          | https://nodejs.org              |
| NPM      | 7.x+           | Bundled with Node.js            |
| Windows  | 10 / 11        | For EXE packaging (or Wine on Linux) |

---

## Project Structure

```
npm-to-exe/
├── build.bat                   ← Windows one-click build (double-click or run)
├── build.sh                    ← Unix/Mac build script
│
├── python-automation/
│   └── build.py                ← Main automation engine
│
├── converter-engine/
│   ├── analyzer.js             ← Project type detection & config
│   └── optimizer.js            ← Asset cleanup & optimization
│
├── electron-runtime/
│   ├── package.json            ← Electron + electron-builder config
│   ├── src/
│   │   └── main.js             ← Electron main process
│   └── preload/
│       └── preload.js          ← Secure IPC bridge
│
├── build-tools/
│   └── icon-generator.js       ← App icon utilities
│
├── demo-app/
│   └── index.html              ← Interactive showcase (place in input-project/ to test)
│
├── input-project/              ← ⬅ PUT YOUR NPM PROJECT HERE
├── output/                     ← ⬅ GENERATED .EXE APPEARS HERE
└── logs/                       ← Build logs for debugging
```

---

## Quick Start

### Step 1 — Add Your Project

Copy your complete NPM web project into the `input-project/` folder:

```
input-project/
├── package.json     ← required
├── src/
├── public/
└── ...
```

Or pass a path directly:
```bat
python python-automation\build.py C:\path\to\your\project
```

### Step 2 — Run the Build

**Windows (recommended):**
```bat
build.bat
```

**Python (cross-platform):**
```bash
python python-automation/build.py
```

### Step 3 — Get Your EXE

After 3–8 minutes, your executable appears in `output/`:
```
output/
├── YourApp Setup 1.0.0.exe     ← NSIS Installer
└── YourApp 1.0.0.exe           ← Portable EXE
```

---

## Supported Input Project Types

| Framework   | Detection Method                     | Build Script     | Output Dir |
|-------------|--------------------------------------|-----------------|------------|
| React (CRA) | `react-dom` in dependencies          | `npm run build`  | `build/`   |
| Vue 3       | `vue` in dependencies                | `npm run build`  | `dist/`    |
| Vite        | `vite` in devDependencies            | `npm run build`  | `dist/`    |
| Next.js     | `next` in dependencies               | `npm run build`  | `.next/`   |
| Webpack     | `webpack` in devDependencies         | `npm run build`  | `dist/`    |
| Angular     | `@angular/core` in dependencies      | `npm run build`  | `dist/`    |
| Parcel      | `parcel` in devDependencies          | `npm run build`  | `dist/`    |
| Vanilla     | No framework detected                | (none needed)    | root       |

---

## How the Build Pipeline Works

```
INPUT PROJECT
      │
      ▼
[1] Project Validation
      Reads package.json, detects framework, validates structure
      │
      ▼
[2] Dependency Installation
      npm ci / npm install (with retry + offline-first)
      │
      ▼
[3] Web Project Build
      npm run build (NODE_ENV=production, source maps off)
      │
      ▼
[4] Electron Runtime Preparation
      Copy build output → electron-runtime/webapp/
      Inject app name/version into main.js + package.json
      │
      ▼
[5] Electron Dependencies
      npm install in electron-runtime/ (electron + electron-builder)
      │
      ▼
[6] EXE Packaging
      electron-builder --win --x64
      Generates NSIS Installer + Portable EXE
      ASAR compression + maximum optimization
      │
      ▼
[7] Output Verification
      Confirm .exe presence, log file size, print report
      │
      ▼
output/*.exe
```

---

## Desktop Runtime Features

### Security Architecture
- Renderer process runs with `nodeIntegration: false`
- `contextIsolation: true` — strict sandbox
- All native APIs exposed via typed `contextBridge` preload
- No direct Node.js access from web layer
- External URL validation before opening

### Native Desktop APIs (via `window.desktopAPI`)
```javascript
// Available in your web app when running as desktop
await window.desktopAPI.getAppInfo()           // App name, version, platform
await window.desktopAPI.openExternal(url)      // Open URL in system browser
await window.desktopAPI.clipboard.write(text)  // Write to clipboard
await window.desktopAPI.clipboard.read()       // Read from clipboard
await window.desktopAPI.dialog.openFile(opts)  // Native file picker
await window.desktopAPI.dialog.saveFile(opts)  // Native save dialog
await window.desktopAPI.window.fullscreen()    // Toggle fullscreen
await window.desktopAPI.window.minimize()      // Minimize window
await window.desktopAPI.window.maximize()      // Maximize/restore

// Detection
if (window.desktopAPI?.isDesktop) {
  // Running as desktop app
}
```

### Web Platform Support
All modern browser APIs are available, including:
- `localStorage`, `sessionStorage`, `IndexedDB`
- Drag & Drop, File API
- WebWorkers, WebAssembly, WebGL
- All CSS features (animations, Grid, Container Queries)
- Canvas, Audio, Video
- Fetch, WebSockets, WebRTC

---

## Special Configurations

### Next.js Projects
Next.js requires static export mode. Add to `next.config.js`:
```js
module.exports = {
  output: 'export',
  // trailingSlash: true,  // recommended
};
```
Then run `npm run build` which will generate a static `out/` directory.

### Projects with API Calls
If your app makes API calls to a backend server:
- External API calls (https://) work normally
- Local `localhost` server calls will fail — embed the server logic or use a remote API
- For full-stack apps, consider embedding an Express server via the Electron main process

### Custom Window Size
Edit `electron-runtime/src/main.js` after build:
```js
width:  1400,
height: 900,
```
Or modify the Python script's `windowConfig` section.

---

## Customization

### Custom App Icon
Place a `256x256` icon file at:
```
electron-runtime/assets/icon.ico
```
Use tools like [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder):
```bash
npx electron-icon-builder --input=your-logo.png --output=electron-runtime/assets/
```

### Custom Build Output Name
The output name comes from `name` in your project's `package.json`. Modify it there.

### Enable DevTools in Production
Edit `electron-runtime/src/main.js`:
```js
// After mainWindow is created:
mainWindow.webContents.openDevTools();
```

---

## Build Logs

All build logs are saved to `logs/` with timestamps:
```
logs/
├── npm-build_20250101_143022.log
├── electron-builder_20250101_143455.log
└── ...
```

Check these files when troubleshooting build failures.

---

## Troubleshooting

| Issue                              | Solution                                                  |
|------------------------------------|-----------------------------------------------------------|
| `npm install` fails                | Check internet connection; logs show exact error          |
| Build script not found             | Ensure `package.json` has a `"build"` script             |
| Empty output after build           | Check build output directory name in `package.json`       |
| `electron-builder` fails           | Ensure Python build completes step 5 first               |
| EXE crashes on startup             | Open DevTools (F12) for JavaScript errors                 |
| White screen                       | Check that `index.html` exists in build output            |
| `localhost` API calls fail         | APIs must be external or embedded in main process         |
| Next.js app not working            | Add `output: 'export'` to `next.config.js`               |

---

## Architecture Notes

### Why Electron?
Electron provides a mature, production-proven desktop runtime built on Chromium + Node.js. It powers VS Code, Slack, Discord, Figma, and thousands of other applications. It guarantees 100% web API compatibility with your existing web project.

### Why Python automation?
Python's standard library handles subprocess management, file operations, and cross-platform path handling more reliably than shell scripts alone. The Python layer provides robust retry logic, structured logging, and graceful error handling.

### Why ASAR packaging?
Electron's ASAR format packs all application files into a single archive, improving load performance, reducing file system overhead, and protecting source code from casual inspection.

---

## Credits

**Developed By Ranjith R**
Built with: Electron, electron-builder, Python, Node.js
