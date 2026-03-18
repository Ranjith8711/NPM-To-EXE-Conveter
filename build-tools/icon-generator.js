'use strict';
/**
 * Build Tools — Icon Generator
 * Generates a default app icon (ICO format) if none provided
 * Developed By Ranjith R
 *
 * For production use: replace with a real icon using tools like:
 *   - electron-icon-builder
 *   - sharp (npm)
 *   - png-to-ico (npm)
 */

const fs   = require('fs');
const path = require('path');

/**
 * Check if icon exists, create a default SVG-based placeholder if not
 */
function ensureIcon(assetsDir, appName) {
  fs.mkdirSync(assetsDir, { recursive: true });

  const icoPath = path.join(assetsDir, 'icon.ico');
  const pngPath = path.join(assetsDir, 'icon.png');
  const svgPath = path.join(assetsDir, 'icon.svg');

  // If ICO already exists, nothing to do
  if (fs.existsSync(icoPath)) {
    console.log('[icons] icon.ico found, skipping generation');
    return icoPath;
  }

  // Write SVG icon
  const initial = (appName || 'A').charAt(0).toUpperCase();
  const svgContent = generateSvgIcon(initial);
  fs.writeFileSync(svgPath, svgContent, 'utf8');
  console.log('[icons] Default SVG icon generated');

  // Note: For real .ico conversion, use:
  // const toIco = require('to-ico');
  // or run: npx electron-icon-builder --input=icon.png --output=./
  console.log('[icons] NOTE: For best results, provide a 256x256 icon.ico in electron-runtime/assets/');
  console.log('[icons] electron-builder will use the SVG as fallback');

  return svgPath;
}

function generateSvgIcon(initial) {
  return `<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1"/>
      <stop offset="100%" style="stop-color:#a855f7"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="52" fill="url(#bg)"/>
  <text x="128" y="180" font-family="Arial,sans-serif" font-size="160"
        font-weight="bold" text-anchor="middle" fill="white">${initial}</text>
</svg>`;
}

module.exports = { ensureIcon, generateSvgIcon };

if (require.main === module) {
  const dir  = process.argv[2] || path.join(__dirname, '..', 'electron-runtime', 'assets');
  const name = process.argv[3] || 'App';
  ensureIcon(dir, name);
}
