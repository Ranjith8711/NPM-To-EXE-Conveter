'use strict';
/**
 * Converter Engine — Project Analyzer
 * Analyzes an NPM project and returns build configuration
 * Developed By Ranjith R
 */

const fs   = require('fs');
const path = require('path');

/**
 * Analyze an NPM project and return a build config object
 * @param {string} projectDir
 * @returns {object}
 */
function analyzeProject(projectDir) {
  const pkgPath = path.join(projectDir, 'package.json');

  if (!fs.existsSync(pkgPath)) {
    throw new Error(`No package.json found in: ${projectDir}`);
  }

  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  const deps    = { ...pkg.dependencies, ...pkg.devDependencies };
  const scripts = pkg.scripts || {};

  // ── Detect framework ───────────────────────────────────
  let framework = 'vanilla';
  const frameworkMap = [
    [['next'],                          'nextjs'],
    [['nuxt'],                          'nuxt'],
    [['react', 'react-dom'],            'react'],
    [['vue', '@vue/core'],              'vue'],
    [['svelte'],                        'svelte'],
    [['solid-js'],                      'solid'],
    [['vite', '@vitejs/plugin-react',
      '@vitejs/plugin-vue'],            'vite'],
    [['webpack', 'webpack-cli'],        'webpack'],
    [['parcel', 'parcel-bundler'],      'parcel'],
    [['@angular/core'],                 'angular'],
    [['ember-cli'],                     'ember'],
  ];

  for (const [keys, name] of frameworkMap) {
    if (keys.some(k => deps[k])) {
      framework = name;
      break;
    }
  }

  // ── Detect build script ────────────────────────────────
  const buildScriptCandidates = ['build', 'build:prod', 'build:production', 'dist', 'compile', 'generate'];
  const buildScript = buildScriptCandidates.find(s => scripts[s]) || null;

  // ── Detect output dir ──────────────────────────────────
  const outputDirCandidates = ['dist', 'build', 'out', '.next', '.nuxt', 'www', 'public'];
  let outputDir = outputDirCandidates.find(d => fs.existsSync(path.join(projectDir, d)));
  if (!outputDir && buildScript) outputDir = 'dist'; // default
  if (!outputDir) outputDir = '.';

  // ── Detect entry point ─────────────────────────────────
  let entryFile = null;
  const entryCandidates = [
    path.join(outputDir, 'index.html'),
    path.join(outputDir, 'index.htm'),
    'index.html',
    'public/index.html',
    'src/index.html',
  ];
  for (const c of entryCandidates) {
    if (fs.existsSync(path.join(projectDir, c))) {
      entryFile = c;
      break;
    }
  }

  // ── Detect if static (no build step needed) ───────────
  const isStatic = !buildScript;

  // ── Window config hints ────────────────────────────────
  const windowConfig = {
    title:           pkg.name || 'My Application',
    width:           1280,
    height:          800,
    minWidth:        800,
    minHeight:       600,
    backgroundColor: '#0a0a0f',
  };

  // Wider window for data-heavy apps
  if (['angular', 'react', 'vue', 'svelte'].includes(framework)) {
    windowConfig.width  = 1400;
    windowConfig.height = 900;
  }

  return {
    name:        pkg.name    || 'my-application',
    version:     pkg.version || '1.0.0',
    description: pkg.description || 'Desktop Application',
    author:      typeof pkg.author === 'string' ? pkg.author : pkg.author?.name || '',
    framework,
    buildScript,
    outputDir,
    entryFile,
    isStatic,
    windowConfig,
    pkg,
    projectDir,
  };
}

/**
 * Validate that a project can be converted
 * @param {object} config - from analyzeProject
 * @returns {string[]} array of warnings (empty = all good)
 */
function validateConfig(config) {
  const warnings = [];

  if (!config.entryFile && !config.buildScript) {
    warnings.push('No index.html and no build script found — converter may need manual configuration');
  }

  if (config.framework === 'nextjs') {
    warnings.push('Next.js apps require static export (next export) for EXE packaging. Ensure "output: export" is set in next.config.js');
  }

  if (config.framework === 'nuxt') {
    warnings.push('Nuxt apps should use "nuxt generate" for static output. Ensure build script produces static files.');
  }

  const pkgSize = JSON.stringify(config.pkg).length;
  if (pkgSize > 50000) {
    warnings.push('Large package.json detected — dependency installation may take longer');
  }

  return warnings;
}

module.exports = { analyzeProject, validateConfig };

// CLI usage
if (require.main === module) {
  const projectDir = process.argv[2] || process.cwd();
  try {
    const config   = analyzeProject(projectDir);
    const warnings = validateConfig(config);
    console.log(JSON.stringify({ config, warnings }, null, 2));
  } catch (e) {
    console.error('Error:', e.message);
    process.exit(1);
  }
}
