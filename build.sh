#!/usr/bin/env bash
# NPM → EXE Converter Build Script
# Developed By Ranjith R

set -e

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║      NPM PROJECT → WINDOWS .EXE CONVERTER           ║"
echo "  ║           Production Build Engine v1.0              ║"
echo "  ║              Developed By Ranjith R                 ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || {
  echo "  [ERROR] Python not found. Install Python 3.8+ from https://python.org"
  exit 1
}
command -v node >/dev/null 2>&1 || {
  echo "  [ERROR] Node.js not found. Install from https://nodejs.org"
  exit 1
}
command -v npm >/dev/null 2>&1 || {
  echo "  [ERROR] NPM not found. Install Node.js from https://nodejs.org"
  exit 1
}

echo "  [OK] Prerequisites verified"
echo ""

PYTHON_CMD="python3"
command -v python3 >/dev/null 2>&1 || PYTHON_CMD="python"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
$PYTHON_CMD "$SCRIPT_DIR/python-automation/build.py" "$@"
