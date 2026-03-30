#!/usr/bin/env bash
# NPM Project → Windows EXE Converter — BEST TEAM
# Unix/Mac build script (requires Wine for actual EXE packaging on Linux/Mac)

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

echo -e ""
echo -e "${CYAN}${BOLD}"
echo    " ╔══════════════════════════════════════════════════════════════╗"
echo    " ║          NPM Project → Windows EXE Converter               ║"
echo    " ║                   Developed by BEST TEAM                   ║"
echo    " ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Dependency checks ───────────────────────────────────────────────────────
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo -e " ${RED}[ERROR]${NC} $1 not found. $2"
    exit 1
  fi
  echo -e " ${GREEN}[OK]${NC} $1 $(command "$1" --version 2>&1 | head -1)"
}

PYTHON=python3
command -v python3 &>/dev/null || PYTHON=python
command -v python  &>/dev/null || { echo -e "${RED}[ERROR]${NC} Python not found."; exit 1; }

check_cmd node  "Install from https://nodejs.org"
check_cmd npm   "Reinstall Node.js from https://nodejs.org"

echo ""

# ── Input project check ─────────────────────────────────────────────────────
if [[ ! -f "input-project/package.json" ]] && [[ $# -eq 0 ]]; then
  echo -e " ${YELLOW}[WARN]${NC} No project found in input-project/"
  echo    "        Copy your NPM project there or pass a path:"
  echo    "        ./build.sh /path/to/your/project"
  exit 1
fi

# ── Run Python automation ───────────────────────────────────────────────────
echo -e " Starting build pipeline..."
echo ""
$PYTHON python-automation/build.py "$@"

EXIT=$?
if [ $EXIT -ne 0 ]; then
  echo -e "\n ${RED}[FAILED]${NC} Build failed. Check logs/ for details."
  exit $EXIT
fi

echo -e "\n ${GREEN}${BOLD}[DONE]${NC} Your EXE is in the output/ folder!"
