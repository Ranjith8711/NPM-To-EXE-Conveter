#!/usr/bin/env python3
"""
Config Validator — NPM to EXE Converter
Run before build to diagnose potential issues
Developed By Ranjith R
"""

import os
import sys
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent

def check(label, condition, fix=""):
    ok = bool(condition)
    icon = "✓" if ok else "✗"
    color = "\033[92m" if ok else "\033[91m"
    reset = "\033[0m"
    print(f"  {color}{icon}{reset}  {label}")
    if not ok and fix:
        print(f"     → {fix}")
    return ok

def main():
    print("\n\033[96m\033[1m  NPM → EXE Converter — Pre-Build Validator\033[0m\n")
    issues = 0

    # ── Tool availability ────────────────────────────────
    print("  Prerequisites:")
    if not check("Python 3.8+", sys.version_info >= (3, 8),
                 "Upgrade Python: https://python.org"):
        issues += 1

    node_ok = shutil.which("node") is not None
    if not check("Node.js installed", node_ok, "Install: https://nodejs.org"):
        issues += 1

    npm_ok = shutil.which("npm") is not None
    if not check("NPM installed", npm_ok, "Install Node.js (includes NPM)"):
        issues += 1

    # ── Project structure ────────────────────────────────
    print("\n  Project structure:")
    input_dir = ROOT / "input-project"
    check("input-project/ folder exists", input_dir.exists(),
          f"Create folder: {input_dir}")

    pkg_path = input_dir / "package.json"
    pkg_ok = pkg_path.exists()
    check("input-project/package.json found", pkg_ok,
          "Place your NPM project in input-project/")

    if pkg_ok:
        try:
            with open(pkg_path) as f:
                pkg = json.load(f)
            check("package.json valid JSON", True)
            check("package.json has 'name' field", bool(pkg.get("name")),
                  "Add: \"name\": \"my-app\" to package.json")
            check("package.json has 'version' field", bool(pkg.get("version")),
                  "Add: \"version\": \"1.0.0\" to package.json")
            scripts = pkg.get("scripts", {})
            has_build = any(s in scripts for s in ["build", "build:prod", "dist", "compile"])
            check("Build script found", has_build or True,  # warn only
                  "If no build script, converter will use project root directly")
        except json.JSONDecodeError as e:
            check(f"package.json parse error: {e}", False)
            issues += 1

    # ── Electron runtime ─────────────────────────────────
    print("\n  Converter engine:")
    check("electron-runtime/src/main.js exists",
          (ROOT / "electron-runtime" / "src" / "main.js").exists())
    check("electron-runtime/preload/preload.js exists",
          (ROOT / "electron-runtime" / "preload" / "preload.js").exists())
    check("electron-runtime/package.json exists",
          (ROOT / "electron-runtime" / "package.json").exists())
    check("python-automation/build.py exists",
          (ROOT / "python-automation" / "build.py").exists())

    # ── Output ───────────────────────────────────────────
    print("\n  Output:")
    output_dir = ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    check("output/ directory ready", True)

    exe_files = list(output_dir.glob("**/*.exe"))
    if exe_files:
        print(f"\n  Previously built EXE files:")
        for exe in exe_files:
            size_mb = exe.stat().st_size / 1024 / 1024
            print(f"    📦  {exe.name}  ({size_mb:.1f} MB)")

    # ── Summary ──────────────────────────────────────────
    print()
    if issues == 0:
        print("  \033[92m✓ All checks passed. Ready to build.\033[0m")
        print("  Run:  python python-automation/build.py\n")
    else:
        print(f"  \033[91m✗ {issues} issue(s) found. Fix them before building.\033[0m\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
