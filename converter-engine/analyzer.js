/**
 * converter-engine/analyzer.js
 * Project type detection & configuration helper
 * BEST TEAM
 */

'use strict';

const fs   = require('fs');
const path = require('path');

const FRAMEWORKS = {
  nextjs:  { deps: ['next'],          build: 'npm run build', outDir: 'out'   },
  react:   { deps: ['react-dom'],     build: 'npm run build', outDir: 'build' },
  vue:     { deps: ['vue'],           build: 'npm run build', outDir: 'dist'  },
  vite:    { devDeps: ['vite'],       build: 'npm run build', outDir: 'dist'  },
  angular: { deps: ['@angular/core'], build: 'npm run build', outDir: 'dist'  },
  webpack: { devDeps: ['webpack'],    build: 'npm run build', outDir: 'dist'  },
  parcel:  { devDeps: ['parcel'],     build: 'npm run build', outDir: 'dist'  },
  vanilla: { deps: [],                build: null,            outDir: '.'     },
};

/**
 * Analyze a project directory and return full metadata.
 * @param {string} projectDir
 * @returns {{ name, version, framework, outDir, hasLockFile, hasBuildScript, scripts }}
 */
function analyzeProject(projectDir) {
  const pkgPath = path.join(projectDir, 'package.json');
  if (!fs.existsSync(pkgPath)) {
    throw new Error(`package.json not found in ${projectDir}`);
  }

  const pkg       = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  const deps      = pkg.dependencies    || {};
  const devDeps   = pkg.devDependencies || {};
  const allDeps   = { ...deps, ...devDeps };
  const scripts   = pkg.scripts || {};

  // Detect framework
  let framework = 'vanilla';
  for (const [fw, cfg] of Object.entries(FRAMEWORKS)) {
    if (fw === 'vanilla') continue;
    const required = [...(cfg.deps || []), ...(cfg.devDeps || [])];
    if (required.some(d => d in allDeps)) {
      framework = fw;
      break;
    }
  }

  const cfg = FRAMEWORKS[framework];

  return {
    name:           pkg.name    || 'unnamed-app',
    version:        pkg.version || '1.0.0',
    framework,
    outDir:         cfg.outDir,
    hasBuildScript: Boolean(scripts.build),
    hasLockFile:    fs.existsSync(path.join(projectDir, 'package-lock.json')) ||
                    fs.existsSync(path.join(projectDir, 'yarn.lock')),
    scripts,
    pkg,
  };
}

/**
 * Validate Next.js projects have static export configured.
 */
function validateNextJs(projectDir) {
  const cfgFiles = ['next.config.js', 'next.config.mjs', 'next.config.ts'];
  for (const f of cfgFiles) {
    const p = path.join(projectDir, f);
    if (fs.existsSync(p)) {
      const src = fs.readFileSync(p, 'utf-8');
      if (!src.includes("output: 'export'") && !src.includes('output: "export"')) {
        return {
          valid: false,
          message: `Next.js project requires static export.\nAdd to ${f}:\n  output: 'export'`,
        };
      }
    }
  }
  return { valid: true };
}

module.exports = { analyzeProject, validateNextJs, FRAMEWORKS };
