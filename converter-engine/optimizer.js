/**
 * converter-engine/optimizer.js
 * Asset cleanup & size optimization before Electron packaging
 * BEST TEAM
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// Extensions to strip from build output (saves space in final EXE)
const REMOVE_EXTENSIONS = new Set([
  '.map',   // source maps
  '.ts',    // leftover TS source
  '.tsx',
  '.jsx',
  '.scss',
  '.sass',
  '.less',
]);

// Files/directories to remove from build output
const REMOVE_NAMES = new Set([
  '.DS_Store',
  'Thumbs.db',
  '.git',
  '.gitignore',
  'node_modules',
  '*.test.js',
  '*.spec.js',
]);

/**
 * Walk a directory recursively.
 * @param {string} dir
 * @returns {string[]} Absolute file paths
 */
function walk(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files   = [];
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) files.push(...walk(full));
    else                  files.push(full);
  }
  return files;
}

/**
 * Strip unnecessary files from a build output directory.
 * @param {string} buildDir
 * @returns {{ removed: number, savedBytes: number }}
 */
function optimizeBuildOutput(buildDir) {
  if (!fs.existsSync(buildDir)) {
    throw new Error(`Build directory not found: ${buildDir}`);
  }

  let removed    = 0;
  let savedBytes = 0;

  const files = walk(buildDir);
  for (const filePath of files) {
    const ext  = path.extname(filePath).toLowerCase();
    const base = path.basename(filePath);

    if (REMOVE_EXTENSIONS.has(ext) || REMOVE_NAMES.has(base)) {
      try {
        const size = fs.statSync(filePath).size;
        fs.unlinkSync(filePath);
        removed++;
        savedBytes += size;
      } catch (_) { /* skip locked files */ }
    }
  }

  // Remove empty directories
  removeEmptyDirs(buildDir);

  return { removed, savedBytes };
}

function removeEmptyDirs(dir) {
  const entries = fs.readdirSync(dir);
  for (const e of entries) {
    const full = path.join(dir, e);
    if (fs.statSync(full).isDirectory()) {
      removeEmptyDirs(full);
      if (fs.readdirSync(full).length === 0) {
        fs.rmdirSync(full);
      }
    }
  }
}

/**
 * Report stats about a directory.
 */
function dirStats(dir) {
  const files     = walk(dir);
  const totalSize = files.reduce((acc, f) => acc + fs.statSync(f).size, 0);
  return { fileCount: files.length, totalSizeMB: (totalSize / 1_048_576).toFixed(2) };
}

module.exports = { optimizeBuildOutput, dirStats };
