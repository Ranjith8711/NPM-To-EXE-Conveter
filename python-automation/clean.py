#!/usr/bin/env python3
"""
Clean Build Artifacts — NPM to EXE Converter
Removes temp dirs, build cache, and optionally output EXEs
Developed By Ranjith R
"""

import os
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent

def confirm(msg):
    try:
        ans = input(f"  {msg} [y/N] ").strip().lower()
        return ans in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False

def remove_dir(path, label):
    if path.exists():
        shutil.rmtree(path)
        print(f"  \033[92m✓\033[0m  Removed {label}")
    else:
        print(f"  \033[2m-  {label} (not found)\033[0m")

def main():
    print("\n\033[96m\033[1m  NPM → EXE Converter — Clean Tool\033[0m\n")

    mode = sys.argv[1] if len(sys.argv) > 1 else "temp"

    if mode in ("all", "--all"):
        print("  This will remove:")
        print("    • .build-temp/  (temp electron packaging dir)")
        print("    • logs/         (build logs)")
        print("    • output/       (generated EXE files)")
        print()
        if not confirm("Are you sure you want to clean everything?"):
            print("  Aborted.\n")
            return

        remove_dir(ROOT / ".build-temp", ".build-temp/")
        remove_dir(ROOT / "logs",        "logs/")
        remove_dir(ROOT / "output",      "output/")

    else:
        print("  Cleaning temporary build artifacts...")
        remove_dir(ROOT / ".build-temp", ".build-temp/")

        logs_dir = ROOT / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            for f in log_files:
                f.unlink()
            if log_files:
                print(f"  \033[92m✓\033[0m  Cleared {len(log_files)} log file(s)")

    print("\n  \033[92mClean complete.\033[0m\n")
    print("  Usage:")
    print("    python python-automation/clean.py         # temp files only")
    print("    python python-automation/clean.py --all   # everything including output/\n")

if __name__ == "__main__":
    main()
