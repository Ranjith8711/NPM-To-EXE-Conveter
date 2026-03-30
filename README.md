# NPM Project → Windows Desktop EXE Converter

> **Production-grade tool** to convert any NPM web project into a standalone Windows `.exe`  
> Developed by **BEST TEAM** · Built with Python & Electron

---

## Quick Start

### 1. Add your project
```
input-project/
├── package.json   ← required
├── src/
└── ...
```

### 2. Run the build

**Windows (double-click or run):**
```
build.bat
```

**Python (cross-platform):**
```bash
python python-automation/build.py
# or with a custom path:
python python-automation/build.py C:\path\to\your\project
```

### 3. Get your EXE
```
output/
├── YourApp Setup 1.0.0.exe   ← NSIS Installer
└── YourApp 1.0.0.exe         ← Portable EXE
```

---

## Requirements

| Tool    | Version | Install                  |
|---------|---------|--------------------------|
| Python  | 3.8+    | https://python.org       |
| Node.js | 16.x+   | https://nodejs.org       |
| npm     | 7.x+    | Bundled with Node.js     |
| Windows | 10/11   | For EXE packaging        |

---

## Project Structure

```
npm-to-exe/
├── build.bat                    ← Windows one-click build
├── build.sh                     ← Unix/Mac build script
├── python-automation/
│   └── build.py                 ← Main automation engine
├── converter-engine/
│   ├── analyzer.js              ← Project type detection & config
│   └── optimizer.js             ← Asset cleanup & optimization
├── electron-runtime/
│   ├── package.json             ← Electron + electron-builder config
│   ├── src/main.js              ← Electron main process
│   └── preload/preload.js       ← Secure IPC bridge
├── build-tools/
│   └── icon-generator.js        ← App icon utilities
├── demo-app/
│   └── index.html               ← Interactive showcase
├── input-project/               ← ⬅ PUT YOUR NPM PROJECT HERE
├── output/                      ← ⬅ GENERATED .EXE APPEARS HERE
└── logs/                        ← Build logs for debugging
```

---

## Supported Frameworks

| Framework  | Detection                   | Output Dir |
|------------|-----------------------------|------------|
| React      | `react-dom` in deps         | `build/`   |
| Vue 3      | `vue` in deps               | `dist/`    |
| Vite       | `vite` in devDeps           | `dist/`    |
| Next.js    | `next` in deps              | `out/`     |
| Webpack    | `webpack` in devDeps        | `dist/`    |
| Angular    | `@angular/core` in deps     | `dist/`    |
| Parcel     | `parcel` in devDeps         | `dist/`    |
| Vanilla    | No framework detected       | root       |

---

## Desktop API

When your web app runs as a packaged EXE, `window.desktopAPI` is injected:

```js
// Detection
if (window.desktopAPI?.isDesktop) { /* running as EXE */ }

// App info
await window.desktopAPI.getAppInfo()

// Clipboard
await window.desktopAPI.clipboard.write(text)
await window.desktopAPI.clipboard.read()

// File dialogs
await window.desktopAPI.dialog.openFile({ filters: [...] })
await window.desktopAPI.dialog.saveFile({ defaultPath: '...' })

// Window controls
await window.desktopAPI.window.fullscreen()
await window.desktopAPI.window.minimize()
await window.desktopAPI.window.maximize()

// Open URLs in system browser
await window.desktopAPI.openExternal('https://example.com')
```

---

## Special Configurations

### Next.js — Static Export Required
Add to `next.config.js`:
```js
module.exports = { output: 'export' }
```

### Custom Icon
Place a `256×256` `.ico` file at:
```
electron-runtime/assets/icon.ico
```

### Custom Window Size
Edit `electron-runtime/src/main.js`:
```js
width:  1400,
height: 900,
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `npm install` fails | Check internet; see `logs/` |
| Build script not found | Add `"build"` to `package.json` scripts |
| White screen after launch | Ensure `index.html` exists in build output |
| EXE crashes on startup | Press F12 for DevTools console |
| Next.js not working | Add `output: 'export'` to next.config.js |

---

**BEST TEAM** · NPM-to-EXE Converter
