#!/usr/bin/env python3
"""
NPM Project → Windows Desktop EXE Converter
Developed by BEST TEAM
Main automation engine
"""

import os
import sys
import json
import time
import shutil
import logging
import argparse
import subprocess
import platform
from pathlib import Path
from datetime import datetime


# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR        = Path(__file__).resolve().parent.parent
INPUT_DIR       = ROOT_DIR / "input-project"
OUTPUT_DIR      = ROOT_DIR / "output"
ELECTRON_DIR    = ROOT_DIR / "electron-runtime"
LOGS_DIR        = ROOT_DIR / "logs"
CONVERTER_DIR   = ROOT_DIR / "converter-engine"
BUILD_TOOLS_DIR = ROOT_DIR / "build-tools"

# ─── ANSI Colors ──────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    DIM    = "\033[2m"


def banner():
    print(f"""
{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════╗
║          NPM Project → Windows EXE Converter                ║
║                   Developed by BEST TEAM                    ║
╚══════════════════════════════════════════════════════════════╝
{C.RESET}""")


def step(num: int, total: int, msg: str):
    print(f"\n{C.BLUE}[{num}/{total}]{C.RESET} {C.BOLD}{msg}{C.RESET}")


def ok(msg: str):
    print(f"  {C.GREEN}✔{C.RESET}  {msg}")


def warn(msg: str):
    print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")


def err(msg: str):
    print(f"  {C.RED}✖{C.RESET}  {msg}")


def info(msg: str):
    print(f"  {C.DIM}→{C.RESET}  {msg}")


# ─── Logger ───────────────────────────────────────────────────────────────────
def setup_logger() -> logging.Logger:
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"build_{ts}.log"

    logger = logging.getLogger("npm-to-exe")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    logger.info(f"Build started — log: {log_file}")
    print(f"  {C.DIM}Log → {log_file}{C.RESET}")
    return logger


# ─── Shell helpers ────────────────────────────────────────────────────────────
def run(cmd: list[str], cwd: Path, logger: logging.Logger,
        env: dict = None, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a subprocess, stream output, log everything."""
    cmd_str = " ".join(str(c) for c in cmd)
    logger.debug(f"RUN: {cmd_str}  (cwd={cwd})")

    merged_env = {**os.environ, **(env or {})}

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=merged_env,
    )

    lines = []
    for line in proc.stdout:
        line = line.rstrip()
        lines.append(line)
        logger.debug(f"  | {line}")
        # Show important lines on console
        if any(kw in line.lower() for kw in ["error", "warn", "failed", "success", "built"]):
            print(f"     {C.DIM}{line}{C.RESET}")

    proc.wait()
    result = subprocess.CompletedProcess(cmd, proc.returncode, "\n".join(lines), "")
    return result


def npm(*args, cwd: Path, logger: logging.Logger, env=None) -> subprocess.CompletedProcess:
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    return run([npm_cmd] + list(args), cwd=cwd, logger=logger, env=env)


def node(*args, cwd: Path, logger: logging.Logger) -> subprocess.CompletedProcess:
    return run(["node"] + list(args), cwd=cwd, logger=logger)


# ─── Step 1: Validate project ─────────────────────────────────────────────────
def validate_project(project_dir: Path, logger: logging.Logger) -> dict:
    pkg_path = project_dir / "package.json"
    if not pkg_path.exists():
        raise FileNotFoundError(f"No package.json found in {project_dir}")

    with open(pkg_path, encoding="utf-8") as f:
        pkg = json.load(f)

    logger.info(f"package.json loaded: name={pkg.get('name')}, version={pkg.get('version')}")
    ok(f"Project: {C.BOLD}{pkg.get('name', 'unnamed')}{C.RESET} v{pkg.get('version', '1.0.0')}")

    all_deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }

    # Framework detection
    framework = "vanilla"
    if "next" in all_deps:
        framework = "nextjs"
    elif "react-dom" in all_deps:
        framework = "react"
    elif "vue" in all_deps:
        framework = "vue"
    elif "vite" in all_deps:
        framework = "vite"
    elif "@angular/core" in all_deps:
        framework = "angular"
    elif "webpack" in all_deps:
        framework = "webpack"
    elif "parcel" in all_deps:
        framework = "parcel"

    info(f"Framework detected: {C.CYAN}{framework}{C.RESET}")

    build_script = pkg.get("scripts", {}).get("build")
    if not build_script and framework != "vanilla":
        warn("No 'build' script found in package.json")

    out_dirs = {
        "react":   "build",
        "nextjs":  "out",
        "vue":     "dist",
        "vite":    "dist",
        "webpack": "dist",
        "angular": "dist",
        "parcel":  "dist",
        "vanilla": ".",
    }

    return {
        "pkg":         pkg,
        "name":        pkg.get("name", "app"),
        "version":     pkg.get("version", "1.0.0"),
        "framework":   framework,
        "has_build":   bool(build_script),
        "output_dir":  out_dirs[framework],
        "project_dir": project_dir,
    }


# ─── Step 2: Install dependencies ─────────────────────────────────────────────
def install_deps(project_dir: Path, logger: logging.Logger):
    lock = project_dir / "package-lock.json"
    cmd  = ["ci"] if lock.exists() else ["install"]
    label = "npm ci" if lock.exists() else "npm install"
    info(f"Running {label} …")

    for attempt in range(1, 4):
        result = npm(*cmd, cwd=project_dir, logger=logger)
        if result.returncode == 0:
            ok("Dependencies installed")
            return
        warn(f"Attempt {attempt}/3 failed — retrying in 3 s …")
        time.sleep(3)

    raise RuntimeError("npm install failed after 3 attempts — check logs/")


# ─── Step 3: Build web project ────────────────────────────────────────────────
def build_web(meta: dict, logger: logging.Logger) -> Path:
    project_dir = meta["project_dir"]

    if meta["framework"] == "vanilla":
        ok("Vanilla project — no build step needed")
        return project_dir

    if not meta["has_build"]:
        warn("No build script — treating as static project")
        return project_dir

    info("Building web project …")
    result = npm("run", "build", cwd=project_dir, logger=logger,
                 env={"NODE_ENV": "production", "GENERATE_SOURCEMAP": "false"})

    if result.returncode != 0:
        raise RuntimeError("Web build failed — check logs/")

    out = project_dir / meta["output_dir"]
    if not out.exists():
        # Try common fallbacks
        for fallback in ["build", "dist", "out", ".next", "www"]:
            if (project_dir / fallback).exists():
                out = project_dir / fallback
                warn(f"Output dir not as expected — using {fallback}/")
                break
        else:
            raise RuntimeError(f"Build output directory not found. Expected: {meta['output_dir']}")

    ok(f"Web build complete → {out.relative_to(project_dir)}/")
    return out


# ─── Step 4: Prepare Electron runtime ─────────────────────────────────────────
def prepare_electron(meta: dict, build_output: Path, logger: logging.Logger):
    webapp_dir = ELECTRON_DIR / "webapp"
    if webapp_dir.exists():
        shutil.rmtree(webapp_dir)

    info(f"Copying build output → electron-runtime/webapp/ …")
    shutil.copytree(str(build_output), str(webapp_dir))
    ok(f"Copied {sum(1 for _ in webapp_dir.rglob('*'))} files")

    # Patch main.js
    main_js = ELECTRON_DIR / "src" / "main.js"
    text = main_js.read_text(encoding="utf-8")
    text = text.replace("__APP_NAME__",    meta["name"])
    text = text.replace("__APP_VERSION__", meta["version"])
    main_js.write_text(text, encoding="utf-8")

    # Patch electron package.json
    epkg_path = ELECTRON_DIR / "package.json"
    epkg = json.loads(epkg_path.read_text(encoding="utf-8"))
    epkg["name"]        = meta["name"]
    epkg["version"]     = meta["version"]
    epkg["description"] = f"{meta['name']} — packaged by BEST TEAM converter"
    epkg["build"]["productName"] = meta["name"].title()
    epkg["build"]["appId"]       = f"com.besttean.{meta['name'].lower().replace(' ','-')}"
    epkg_path.write_text(json.dumps(epkg, indent=2), encoding="utf-8")

    ok("Electron runtime configured")


# ─── Step 5: Install Electron deps ────────────────────────────────────────────
def install_electron_deps(logger: logging.Logger):
    info("Installing Electron dependencies …")
    result = npm("install", cwd=ELECTRON_DIR, logger=logger)
    if result.returncode != 0:
        raise RuntimeError("Electron npm install failed")
    ok("Electron dependencies ready")


# ─── Step 6: Package EXE ──────────────────────────────────────────────────────
def package_exe(meta: dict, logger: logging.Logger):
    info("Running electron-builder …")
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    result = run(
        [npm_cmd, "run", "dist"],
        cwd=ELECTRON_DIR,
        logger=logger,
    )
    if result.returncode != 0:
        raise RuntimeError("electron-builder failed — check logs/")
    ok("EXE packaging complete")


# ─── Step 7: Verify output ────────────────────────────────────────────────────
def verify_output(meta: dict, logger: logging.Logger):
    dist_dir = ELECTRON_DIR / "dist"
    exes = list(dist_dir.glob("**/*.exe")) if dist_dir.exists() else []

    if not exes:
        raise RuntimeError("No .exe files found in electron-runtime/dist/")

    OUTPUT_DIR.mkdir(exist_ok=True)
    final = []
    for exe in exes:
        dest = OUTPUT_DIR / exe.name
        shutil.copy2(str(exe), str(dest))
        size_mb = dest.stat().st_size / 1_048_576
        ok(f"{exe.name}  ({size_mb:.1f} MB)")
        final.append(dest)
        logger.info(f"Output: {dest} ({size_mb:.1f} MB)")

    return final


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    banner()

    parser = argparse.ArgumentParser(description="NPM → EXE Converter by BEST TEAM")
    parser.add_argument("project", nargs="?", default=str(INPUT_DIR),
                        help="Path to your NPM project (default: input-project/)")
    parser.add_argument("--skip-web-build", action="store_true",
                        help="Skip npm run build (use if already built)")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        err(f"Project directory not found: {project_dir}")
        sys.exit(1)

    logger = setup_logger()
    start  = time.time()
    TOTAL  = 7

    try:
        step(1, TOTAL, "Validating project")
        meta = validate_project(project_dir, logger)

        step(2, TOTAL, "Installing project dependencies")
        install_deps(project_dir, logger)

        step(3, TOTAL, "Building web project")
        if args.skip_web_build:
            warn("--skip-web-build: skipping npm run build")
            build_output = project_dir / meta["output_dir"]
        else:
            build_output = build_web(meta, logger)

        step(4, TOTAL, "Preparing Electron runtime")
        prepare_electron(meta, build_output, logger)

        step(5, TOTAL, "Installing Electron dependencies")
        install_electron_deps(logger)

        step(6, TOTAL, "Packaging Windows EXE")
        package_exe(meta, logger)

        step(7, TOTAL, "Verifying output")
        outputs = verify_output(meta, logger)

        elapsed = time.time() - start
        print(f"""
{C.GREEN}{C.BOLD}
╔══════════════════════════════════════════╗
║          BUILD SUCCESSFUL! 🎉            ║
╚══════════════════════════════════════════╝
{C.RESET}
  Time:    {elapsed/60:.1f} min
  Output:  {OUTPUT_DIR}/
  Files:   {len(outputs)} executable(s)

  {C.DIM}Developed by BEST TEAM{C.RESET}
""")

    except Exception as exc:
        elapsed = time.time() - start
        logger.exception("Build failed")
        print(f"""
{C.RED}{C.BOLD}
╔══════════════════════════════════════════╗
║              BUILD FAILED ✖              ║
╚══════════════════════════════════════════╝
{C.RESET}
  Error:  {exc}
  Time:   {elapsed/60:.1f} min
  Logs:   {LOGS_DIR}/

  Run with --help for usage information.
""")
        sys.exit(1)


if __name__ == "__main__":
    main()
