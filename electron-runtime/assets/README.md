# electron-runtime/assets/

Place your application icon files here.

## Required for Windows packaging

| File         | Size    | Purpose                          |
|--------------|---------|----------------------------------|
| `icon.ico`   | 256x256 | Windows EXE icon (required)      |
| `icon.png`   | 512x512 | Optional, used by electron-builder |

## Generate icon from PNG

```bash
# Using electron-icon-builder
npm install -g electron-icon-builder
electron-icon-builder --input=your-logo.png --output=./

# Using png-to-ico
npm install -g png-to-ico
png-to-ico your-logo.png > icon.ico
```

## Fallback

If no `icon.ico` is provided, electron-builder uses a default Electron icon.
The `icon.svg` in this folder is a placeholder — convert it to ICO for production.

---
Developed By Ranjith R
