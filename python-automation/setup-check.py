#!/usr/bin/env python3
"""
setup-check.py — Environment validator
Run this before your first build to confirm everything is installed correctly.
Developed by BEST TEAM
"""

import sys
import subprocess
import platform
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"


def ok(label, value=""):
    print(f"  {C.GREEN}✔{C.RESET}  {label:<30} {C.DIM}{value}{C.RESET}")


def fail(label, hint=""):
    print(f"  {C.RED}✖{C.RESET}  {label:<30} {C.RED}{hint}{C.RESET}")


def warn(label, hint=""):
    print(f"  {C.YELLOW}⚠{C.RESET}  {label:<30} {C.YELLOW}{hint}{C.RESET}")


def check_cmd(cmd: list[str], label: str, min_version: str = None) -> bool:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        version = (r.stdout + r.stderr).strip().splitlines()[0]
        ok(label, version)
        return True
    except FileNotFoundError:
        fail(label, "not found in PATH")
        return False
    except Exception as e:
        fail(label, str(e))
        return False


def check_file(path: Path, label: str) -> bool:
    if path.exists():
        ok(label, str(path.relative_to(ROOT_DIR)))
        return True
    else:
        fail(label, f"missing: {path}")
        return False


def check_dir(path: Path, label: str) -> bool:
    if path.is_dir():
        ok(label)
        return True
    else:
        warn(label, "directory missing — will be created automatically")
        return False


def main():
    print(f"""
{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════╗
║         NPM → EXE Converter — Environment Check            ║
║                    Developed by BEST TEAM                   ║
╚══════════════════════════════════════════════════════════════╝
{C.RESET}""")

    errors   = 0
    warnings = 0

    # ── System ────────────────────────────────────────────────────────────────
    print(f"{C.BOLD}System{C.RESET}")
    ok("Platform", platform.platform())
    ok("Python",   sys.version.split()[0])
    print()

    # ── Required tools ────────────────────────────────────────────────────────
    print(f"{C.BOLD}Required Tools{C.RESET}")

    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    node_ok  = check_cmd(["node", "--version"],   "Node.js  (≥16)")
    npm_ok   = check_cmd([npm_cmd, "--version"],  "npm      (≥7)")
    py_ok    = check_cmd([sys.executable, "--version"], "Python   (≥3.8)")

    if not node_ok: errors += 1
    if not npm_ok:  errors += 1
    print()

    # ── Wine (Linux/Mac only) ──────────────────────────────────────────────────
    if platform.system() != "Windows":
        print(f"{C.BOLD}Windows Packaging (Linux/Mac){C.RESET}")
        wine_ok = check_cmd(["wine", "--version"], "Wine (for EXE packaging)")
        if not wine_ok:
            warn("Wine", "EXE packaging may fail on non-Windows without Wine")
            warnings += 1
        print()

    # ── Project files ─────────────────────────────────────────────────────────
    print(f"{C.BOLD}Project Structure{C.RESET}")
    files = [
        (ROOT_DIR / "python-automation" / "build.py",        "build.py"),
        (ROOT_DIR / "electron-runtime"  / "src"  / "main.js","electron main.js"),
        (ROOT_DIR / "electron-runtime"  / "preload" / "preload.js", "preload.js"),
        (ROOT_DIR / "electron-runtime"  / "package.json",    "electron package.json"),
        (ROOT_DIR / "converter-engine"  / "analyzer.js",     "analyzer.js"),
        (ROOT_DIR / "converter-engine"  / "optimizer.js",    "optimizer.js"),
    ]
    for path, label in files:
        if not check_file(path, label):
            errors += 1

    print()

    # ── Directories ───────────────────────────────────────────────────────────
    print(f"{C.BOLD}Directories{C.RESET}")
    dirs = [
        (ROOT_DIR / "input-project",            "input-project/"),
        (ROOT_DIR / "output",                   "output/"),
        (ROOT_DIR / "logs",                     "logs/"),
        (ROOT_DIR / "electron-runtime/assets",  "electron-runtime/assets/"),
    ]
    for path, label in dirs:
        if not check_dir(path, label):
            warnings += 1
            path.mkdir(parents=True, exist_ok=True)

    print()

    # ── Input project ─────────────────────────────────────────────────────────
    print(f"{C.BOLD}Input Project{C.RESET}")
    pkg = ROOT_DIR / "input-project" / "package.json"
    if pkg.exists():
        import json
        data = json.loads(pkg.read_text())
        ok("package.json found", f"name={data.get('name')} version={data.get('version')}")
    else:
        warn("No package.json in input-project/",
             "Copy your NPM project there before building")
        warnings += 1

    print()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("─" * 55)
    if errors == 0 and warnings == 0:
        print(f"  {C.GREEN}{C.BOLD}✔  All checks passed. Ready to build!{C.RESET}")
        print(f"  {C.DIM}Run: build.bat  (Windows)  or  python python-automation/build.py{C.RESET}")
    elif errors == 0:
        print(f"  {C.YELLOW}⚠  {warnings} warning(s). You can proceed, but review above.{C.RESET}")
    else:
        print(f"  {C.RED}✖  {errors} error(s) must be fixed before building.{C.RESET}")
        if warnings:
            print(f"  {C.YELLOW}⚠  {warnings} warning(s) also noted.{C.RESET}")
    print()

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
