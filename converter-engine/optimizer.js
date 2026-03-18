'use strict';
/**
 * Asset Optimizer
 * Post-build optimization for web assets before Electron packaging
 * Developed By Ranjith R
 */

const fs   = require('fs');
const path = require('path');

/**
 * Optimize build output directory
 * Removes unnecessary files, logs stats
 */
function optimizeAssets(buildDir) {
  if (!fs.existsSync(buildDir)) {
    console.warn(`[optimizer] Directory not found: ${buildDir}`);
    return { removed: 0, savedBytes: 0 };
  }

  let removed    = 0;
  let savedBytes = 0;

  // Patterns to remove from build output
  const removePatterns = [
    /\.map$/i,          // Source maps (reduce size)
    /\.LICENSE\.txt$/i, // License files bundled by webpack
    /thumbs\.db$/i,     // Windows thumbnail cache
    /\.DS_Store$/i,     // macOS metadata
    /desktop\.ini$/i,   // Windows folder config
  ];

  walkDir(buildDir, (filePath) => {
    const basename = path.basename(filePath);
    if (removePatterns.some(p => p.test(basename))) {
      try {
        const size = fs.statSync(filePath).size;
        fs.unlinkSync(filePath);
        removed++;
        savedBytes += size;
      } catch { /* ignore */ }
    }
  });

  return { removed, savedBytes };
}

/**
 * Walk directory recursively
 */
function walkDir(dir, fn) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) walkDir(fullPath, fn);
    else fn(fullPath);
  }
}

/**
 * Get directory stats
 */
function getDirStats(dir) {
  let totalSize  = 0;
  let fileCount  = 0;
  const extMap   = {};

  walkDir(dir, (filePath) => {
    const size = fs.statSync(filePath).size;
    totalSize += size;
    fileCount++;
    const ext = path.extname(filePath).toLowerCase() || '(no ext)';
    extMap[ext] = (extMap[ext] || 0) + 1;
  });

  return { totalSize, fileCount, extMap };
}

module.exports = { optimizeAssets, getDirStats, walkDir };

if (require.main === module) {
  const dir = process.argv[2];
  if (!dir) { console.error('Usage: node optimizer.js <build-dir>'); process.exit(1); }
  const before = getDirStats(dir);
  const result = optimizeAssets(dir);
  const after  = getDirStats(dir);
  console.log(`Removed: ${result.removed} files, saved ${(result.savedBytes/1024).toFixed(1)} KB`);
  console.log(`Total: ${after.fileCount} files, ${(after.totalSize/1024/1024).toFixed(2)} MB`);
}
