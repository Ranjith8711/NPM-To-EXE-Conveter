#!/usr/bin/env python3
"""
NPM Project -> Windows Desktop EXE Converter
Python Automation Engine v1.0
Developed By Ranjith R
"""

import os
import sys
import json
import shutil
import subprocess
import time
import platform
import re
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
#  ANSI Colors
# ─────────────────────────────────────────────
class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    DIM     = "\033[2m"

def banner():
    print(Colors.CYAN + Colors.BOLD)
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        NPM PROJECT → WINDOWS .EXE CONVERTER             ║")
    print("║              Production Build Engine v1.0               ║")
    print("║                                                          ║")
    print("║              Developed By Ranjith R                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(Colors.RESET)

def log(level, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {
        "info":    Colors.BLUE    + "[INFO]" + Colors.RESET,
        "success": Colors.GREEN   + "[OK  ]" + Colors.RESET,
        "warn":    Colors.YELLOW  + "[WARN]" + Colors.RESET,
        "error":   Colors.RED     + "[ERR ]" + Colors.RESET,
        "step":    Colors.MAGENTA + "[STEP]" + Colors.RESET,
        "build":   Colors.CYAN    + "[BUILD]" + Colors.RESET,
    }
    icon = icons.get(level, "[    ]")
    print(Colors.DIM + ts + Colors.RESET + " " + icon + " " + msg)

def separator(title=""):
    width = 60
    if title:
        pad = (width - len(title) - 2) // 2
        line = "-" * pad + " " + title + " " + "-" * pad
        print("\n" + Colors.CYAN + Colors.BOLD + line + Colors.RESET + "\n")
    else:
        print("\n" + Colors.DIM + "-" * width + Colors.RESET + "\n")

# ─────────────────────────────────────────────
#  Paths  — ROOT is the folder containing this
#  script's parent, i.e. the converter root.
#  build.py lives at:  <root>/python-automation/build.py
#  So:  __file__  -> python-automation/build.py
#       .parent   -> python-automation/
#       .parent   -> <root>/
# ─────────────────────────────────────────────
ROOT_DIR     = Path(__file__).resolve().parent.parent
INPUT_DIR    = ROOT_DIR / "input-project"
ELECTRON_DIR = ROOT_DIR / "electron-runtime"
OUTPUT_DIR   = ROOT_DIR / "output"
LOGS_DIR     = ROOT_DIR / "logs"
TEMP_DIR     = ROOT_DIR / ".build-temp"
DEMO_DIR     = ROOT_DIR / "demo-app"

MAX_RETRIES = 3

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def write_log(name, content):
    ensure_dir(LOGS_DIR)
    log_file = LOGS_DIR / (name + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".log")
    log_file.write_text(content, encoding="utf-8")
    return log_file

def run_cmd(cmd, cwd=None, env=None, capture=False, label=""):
    attempt = 0
    while attempt < MAX_RETRIES:
        attempt += 1
        if label:
            log("build", label + " (attempt " + str(attempt) + "/" + str(MAX_RETRIES) + ")")
        try:
            if capture:
                result = subprocess.run(
                    cmd, shell=True,
                    cwd=str(cwd) if cwd else None,
                    capture_output=True, text=True, env=env
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    cmd, shell=True,
                    cwd=str(cwd) if cwd else None,
                    env=env
                )
                if result.returncode == 0:
                    return result.returncode, "", ""
                if attempt < MAX_RETRIES:
                    log("warn", "Command failed (exit " + str(result.returncode) + "), retrying in 3s...")
                    time.sleep(3)
                else:
                    return result.returncode, "", ""
        except Exception as e:
            log("error", "Exception: " + str(e))
            if attempt >= MAX_RETRIES:
                return 1, "", str(e)
            time.sleep(2)
    return 1, "", "Max retries exceeded"

def sanitize_name(name):
    return re.sub(r'[^a-z0-9\-]', '-', name.lower()).strip('-') or "my-app"

# ─────────────────────────────────────────────
#  Step 1: Prerequisites
# ─────────────────────────────────────────────
def check_prerequisites():
    separator("PREREQUISITES CHECK")
    ok = True
    for tool, label in [("node --version", "Node.js"), ("npm --version", "NPM")]:
        code, out, _ = run_cmd(tool, capture=True)
        if code == 0:
            version = out.strip().splitlines()[0] if out.strip() else "ok"
            log("success", label + ": " + version)
        else:
            log("error", label + " not found — please install it")
            ok = False
    if not ok:
        print()
        print("  Install Node.js (includes NPM) from: https://nodejs.org")
        print()
        sys.exit(1)

# ─────────────────────────────────────────────
#  Step 2: Validate Input Project
# ─────────────────────────────────────────────
def validate_input_project():
    separator("PROJECT VALIDATION")

    # CLI argument overrides the default input-project/ folder
    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1]).resolve()
    else:
        project_dir = INPUT_DIR

    log("info", "Looking for project in: " + str(project_dir))

    # ── Folder missing entirely ───────────────────────────────────
    if not project_dir.exists():
        _show_no_project_error(project_dir)

    # ── Folder exists but no package.json ────────────────────────
    pkg_path = project_dir / "package.json"

    if not pkg_path.exists():
        # Maybe user put project inside a sub-folder of input-project/
        found_sub = None
        try:
            for item in project_dir.iterdir():
                if item.is_dir() and (item / "package.json").exists():
                    found_sub = item
                    break
        except Exception:
            pass

        if found_sub:
            log("info", "Found project in sub-folder: " + found_sub.name)
            log("info", "Using: " + str(found_sub))
            project_dir = found_sub
            pkg_path = found_sub / "package.json"
        else:
            _show_no_project_error(project_dir)

    # ── Read package.json ─────────────────────────────────────────
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except json.JSONDecodeError as e:
        log("error", "package.json is malformed: " + str(e))
        sys.exit(1)

    app_name    = pkg.get("name", "MyApplication")
    app_version = pkg.get("version", "1.0.0")
    app_desc    = pkg.get("description", "Desktop Application")

    # Detect type
    deps     = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    all_deps = {}
    all_deps.update(deps)
    all_deps.update(dev_deps)
    scripts  = pkg.get("scripts", {})

    project_type = "vanilla"
    if "react" in all_deps or "react-dom" in all_deps:
        project_type = "react"
    elif "vue" in all_deps:
        project_type = "vue"
    elif "vite" in all_deps:
        project_type = "vite"
    elif "webpack" in all_deps or "webpack-cli" in all_deps:
        project_type = "webpack"
    elif "next" in all_deps:
        project_type = "next"
    elif "@angular/core" in all_deps:
        project_type = "angular"

    # Detect build script
    build_script = None
    for candidate in ["build", "build:prod", "dist", "compile", "generate"]:
        if candidate in scripts:
            build_script = candidate
            break

    # Detect build output dir (check if it already exists from a previous build)
    build_output = None
    for candidate in ["dist", "build", "out", "public", ".next", "www"]:
        if (project_dir / candidate).exists():
            build_output = candidate
            break
    if not build_output and build_script:
        build_output = "dist"
    if not build_output:
        build_output = "."

    log("success", "Project:     " + app_name + " v" + app_version)
    log("info",    "Type:        " + project_type.upper())
    log("info",    "Build script: " + ("npm run " + build_script if build_script else "[none - static project]"))
    log("info",    "Build output: " + build_output)

    return {
        "dir":          project_dir,
        "pkg":          pkg,
        "name":         app_name,
        "version":      app_version,
        "description":  app_desc,
        "type":         project_type,
        "build_script": build_script,
        "build_output": build_output,
        "scripts":      scripts,
    }

def _show_no_project_error(project_dir):
    print()
    print(Colors.RED + "  ╔══════════════════════════════════════════════════════════╗")
    print("  ║  NO PROJECT FOUND                                        ║")
    print("  ╚══════════════════════════════════════════════════════════╝" + Colors.RESET)
    print()
    print("  Expected to find your project at:")
    print("  " + Colors.YELLOW + str(project_dir) + Colors.RESET)
    print()
    print("  HOW TO FIX:")
    print("  ─────────────────────────────────────────────────────────")
    print("  1. Copy your entire NPM project folder contents into:")
    print("     " + Colors.CYAN + str(INPUT_DIR) + Colors.RESET)
    print()
    print("     Your input-project\\ folder should look like:")
    print("       input-project\\")
    print("         package.json    <-- this file must exist")
    print("         src\\")
    print("         public\\")
    print("         ...")
    print()
    print("  2. Then run build.bat again.")
    print()
    print("  ─────────────────────────────────────────────────────────")
    print("  OR: To test with the built-in demo app right now,")
    print("  copy the demo-app\\ contents into input-project\\")
    print()
    print("  OR: Drag your project folder onto build.bat to specify")
    print("  a custom path directly.")
    print("  ─────────────────────────────────────────────────────────")
    print()

    # Offer to auto-copy demo app
    if DEMO_DIR.exists() and (DEMO_DIR / "package.json").exists():
        try:
            answer = input("  Copy the built-in demo app and run now? (Y/N): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            answer = "n"

        if answer == "y":
            ensure_dir(INPUT_DIR)
            for item in DEMO_DIR.iterdir():
                dest = INPUT_DIR / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(str(item), str(dest))
                else:
                    shutil.copy2(str(item), str(dest))
            print()
            log("success", "Demo app copied to input-project\\")
            print()
            # Restart validation with new project
            return  # caller will re-call us — but we need to restart main
        else:
            sys.exit(0)
    else:
        sys.exit(1)

# ─────────────────────────────────────────────
#  Step 3: Install Dependencies
# ─────────────────────────────────────────────
def install_project_deps(project):
    separator("INSTALLING PROJECT DEPENDENCIES")
    project_dir = project["dir"]
    nm = project_dir / "node_modules"

    if nm.exists():
        log("info", "node_modules found — running npm install to ensure up to date")

    code, out, err = run_cmd("npm install", cwd=project_dir, label="npm install")

    if code != 0:
        log("error", "Dependency installation failed")
        write_log("npm-install", err)
        sys.exit(1)

    log("success", "Dependencies installed")

# ─────────────────────────────────────────────
#  Step 4: Build the Web Project
# ─────────────────────────────────────────────
def build_web_project(project):
    separator("BUILDING WEB PROJECT")

    build_script = project["build_script"]

    if not build_script:
        log("info", "No build script — using project as-is (static project)")
        return

    log("build", "Running: npm run " + build_script)

    env = os.environ.copy()
    env["NODE_ENV"] = "production"
    env["GENERATE_SOURCEMAP"] = "false"
    env["INLINE_RUNTIME_CHUNK"] = "false"

    code, out, err = run_cmd(
        "npm run " + build_script,
        cwd=project["dir"],
        env=env,
        label="npm run " + build_script,
        capture=True
    )

    write_log("npm-build", out + "\n--- STDERR ---\n" + err)

    if code != 0:
        log("error", "Web project build failed — last 20 lines:")
        lines = (out + "\n" + err).splitlines()
        for line in lines[-20:]:
            print("    " + Colors.RED + line + Colors.RESET)
        log("info", "Full log saved to logs/ folder")
        sys.exit(1)

    log("success", "Web project built successfully")

    output_path = project["dir"] / project["build_output"]
    if output_path.exists():
        files = list(output_path.rglob("*"))
        size  = sum(f.stat().st_size for f in files if f.is_file())
        log("info", "Build output: " + str(len(files)) + " files, " + str(size // 1024) + " KB")

# ─────────────────────────────────────────────
#  Step 5: Prepare Electron Runtime
# ─────────────────────────────────────────────
def prepare_electron_runtime(project):
    separator("PREPARING ELECTRON RUNTIME")
    ensure_dir(TEMP_DIR)

    electron_dest = TEMP_DIR / "electron-app"

    if electron_dest.exists():
        shutil.rmtree(str(electron_dest))

    shutil.copytree(str(ELECTRON_DIR), str(electron_dest))
    log("success", "Electron runtime template copied")

    # Copy built web assets into electron-app/webapp
    webapp_dest = electron_dest / "webapp"
    if webapp_dest.exists():
        shutil.rmtree(str(webapp_dest))

    project_dir  = project["dir"]
    build_output = project["build_output"]

    if project["build_script"] and build_output != ".":
        source_path = project_dir / build_output
    else:
        source_path = project_dir

    shutil.copytree(
        str(source_path),
        str(webapp_dest),
        ignore=shutil.ignore_patterns(
            "node_modules", ".git", ".env", ".env.*",
            "*.log", ".DS_Store", "Thumbs.db"
        )
    )

    file_count = len(list(webapp_dest.rglob("*")))
    log("success", "Web assets copied — " + str(file_count) + " items")

    # Patch package.json
    electron_pkg_path = electron_dest / "package.json"
    with open(str(electron_pkg_path), "r", encoding="utf-8") as f:
        electron_pkg = json.load(f)

    electron_pkg["name"]        = sanitize_name(project["name"])
    electron_pkg["version"]     = project["version"]
    electron_pkg["description"] = project["description"]
    electron_pkg["build"]["productName"] = project["name"]
    electron_pkg["build"]["appId"] = "com.desktop." + sanitize_name(project["name"])
    electron_pkg["build"]["directories"]["output"] = str(OUTPUT_DIR)

    with open(str(electron_pkg_path), "w", encoding="utf-8") as f:
        json.dump(electron_pkg, f, indent=2)

    log("success", "Electron package.json configured")

    # Patch main.js
    main_js_path = electron_dest / "src" / "main.js"
    if main_js_path.exists():
        content = main_js_path.read_text(encoding="utf-8")
        content = content.replace("__APP_NAME__",    project["name"])
        content = content.replace("__APP_VERSION__", project["version"])
        main_js_path.write_text(content, encoding="utf-8")
        log("success", "main.js patched with app name and version")

    return electron_dest

# ─────────────────────────────────────────────
#  Step 6: Install Electron Dependencies
# ─────────────────────────────────────────────
def install_electron_deps(electron_dest):
    separator("INSTALLING ELECTRON DEPENDENCIES")
    log("info", "Installing Electron + electron-builder (may take a few minutes)...")

    env = os.environ.copy()
    env["ELECTRON_MIRROR"] = "https://npmmirror.com/mirrors/electron/"

    code, out, err = run_cmd(
        "npm install",
        cwd=electron_dest,
        env=env,
        label="npm install (electron)"
    )

    if code != 0:
        log("error", "Electron dependency installation failed")
        write_log("electron-install", out + err)
        sys.exit(1)

    log("success", "Electron dependencies installed")

# ─────────────────────────────────────────────
#  Step 7: Package EXE
# ─────────────────────────────────────────────
def package_exe(electron_dest, project):
    separator("PACKAGING WINDOWS EXECUTABLE")
    ensure_dir(OUTPUT_DIR)

    log("build", "Running electron-builder — this takes 2-5 minutes...")

    env = os.environ.copy()
    env["CSC_IDENTITY_AUTO_DISCOVERY"] = "false"

    output_str = str(OUTPUT_DIR).replace("\\", "/")
    cmd = 'npx electron-builder --win --x64 --config.directories.output="' + output_str + '"'

    code, out, err = run_cmd(cmd, cwd=electron_dest, env=env, label="electron-builder", capture=True)
    write_log("electron-builder", out + "\n--- STDERR ---\n" + err)

    if code != 0:
        log("warn", "Full build failed, trying portable EXE only...")
        cmd2 = 'npx electron-builder --win portable --x64 --config.directories.output="' + output_str + '"'
        code, out, err = run_cmd(cmd2, cwd=electron_dest, env=env, label="electron-builder portable", capture=True)
        write_log("electron-builder-portable", out + "\n--- STDERR ---\n" + err)

        if code != 0:
            log("error", "EXE packaging failed. Check logs/ folder.")
            sys.exit(1)

    exe_files = list(OUTPUT_DIR.glob("**/*.exe"))
    if not exe_files:
        log("error", "No .exe found in output/ after packaging")
        sys.exit(1)

    log("success", str(len(exe_files)) + " EXE file(s) generated")
    return exe_files

# ─────────────────────────────────────────────
#  Final Report
# ─────────────────────────────────────────────
def final_report(project, exe_files, start_time):
    separator("BUILD COMPLETE")
    elapsed = time.time() - start_time

    print(Colors.GREEN + Colors.BOLD)
    print("  SUCCESS!")
    print(Colors.RESET)

    log("success", "Application:  " + project["name"] + " v" + project["version"])
    log("success", "Build time:   " + str(round(elapsed, 1)) + " seconds")
    log("success", "Output dir:   " + str(OUTPUT_DIR))
    print()

    for exe in exe_files:
        size_mb = exe.stat().st_size / (1024 * 1024)
        print("  " + Colors.CYAN + "  " + exe.name + Colors.RESET + "  (" + str(round(size_mb, 1)) + " MB)")

    print()
    print(Colors.DIM + "  The .exe is fully self-contained — no Node.js required on target machine." + Colors.RESET)
    print(Colors.DIM + "  Developed By Ranjith R " + Colors.RESET)
    print()

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    start_time = time.time()
    banner()

    log("info", "Converter root: " + str(ROOT_DIR))
    log("info", "Input project:  " + str(INPUT_DIR))
    log("info", "Output folder:  " + str(OUTPUT_DIR))
    print()

    check_prerequisites()
    project       = validate_input_project()
    install_project_deps(project)
    build_web_project(project)
    electron_dest = prepare_electron_runtime(project)
    install_electron_deps(electron_dest)
    exe_files     = package_exe(electron_dest, project)
    final_report(project, exe_files, start_time)

if __name__ == "__main__":
    main()
