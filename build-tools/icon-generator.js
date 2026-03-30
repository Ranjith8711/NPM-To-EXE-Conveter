/**
 * build-tools/icon-generator.js
 * App icon utilities for BEST TEAM converter
 *
 * Usage:
 *   node build-tools/icon-generator.js --input logo.png --output electron-runtime/assets/
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// Minimal 1×1 px transparent ICO (fallback if no icon supplied)
// This is a valid ICO binary — 40 bytes
const FALLBACK_ICO_B64 =
  'AAABAAEAAQEAAAEAGAAAACYAAABQAAAAEAAAABAAAAABABgA' +
  'AAAAAAAAAAAAAAAAAAAAAAAAAAAA';

/**
 * Ensure an icon.ico exists at the target path.
 * If the user supplies a PNG, convert it (requires `sharp` or falls back to placeholder).
 *
 * @param {string|null} inputPng  - Path to a source PNG (optional)
 * @param {string}      outputDir - Directory to write icon.ico into
 */
async function ensureIcon(inputPng, outputDir) {
  const destIco = path.join(outputDir, 'icon.ico');

  // If dest already exists, nothing to do
  if (fs.existsSync(destIco)) return { used: 'existing', path: destIco };

  fs.mkdirSync(outputDir, { recursive: true });

  if (inputPng && fs.existsSync(inputPng)) {
    // Attempt to use `sharp` for proper conversion (optional dep)
    try {
      const sharp = require('sharp');
      const sizes  = [16, 32, 48, 64, 128, 256];
      // sharp can write .ico on Windows via toFormat('ico') in some versions
      // For cross-platform, write a 256px PNG and rely on electron-builder
      const outPng = path.join(outputDir, 'icon.png');
      await sharp(inputPng).resize(256, 256).png().toFile(outPng);
      console.log(`✔  Icon resized: ${outPng}`);
      return { used: 'sharp', path: outPng };
    } catch (_) {
      console.warn('  sharp not available — using fallback icon');
    }
  }

  // Write minimal placeholder ICO
  const buf = Buffer.from(FALLBACK_ICO_B64, 'base64');
  fs.writeFileSync(destIco, buf);
  console.log(`  ℹ  Placeholder icon written: ${destIco}`);
  return { used: 'placeholder', path: destIco };
}

// ─── CLI ──────────────────────────────────────────────────────────────────────
if (require.main === module) {
  const args  = process.argv.slice(2);
  const input = args[args.indexOf('--input')  + 1] || null;
  const outDir= args[args.indexOf('--output') + 1] ||
                path.join(__dirname, '..', 'electron-runtime', 'assets');

  ensureIcon(input, outDir)
    .then(r => console.log('Icon ready:', r))
    .catch(e => { console.error(e.message); process.exit(1); });
}

module.exports = { ensureIcon };
