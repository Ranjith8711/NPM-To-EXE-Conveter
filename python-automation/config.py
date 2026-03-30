#!/usr/bin/env python3
"""
python-automation/config.py
Project-level configuration loader for the BEST TEAM converter.

A project can optionally include a `converter.config.json` at its root
to override build settings. The CLI build.py merges these on top of defaults.

Example converter.config.json:
{
  "window": { "width": 1400, "height": 900 },
  "icon": "./assets/logo.png",
  "skipOptimize": false,
  "extraElectronConfig": {
    "alwaysOnTop": false
  }
}
"""

import json
from pathlib import Path
from typing import Any


CONFIG_FILENAME = "converter.config.json"

DEFAULTS: dict[str, Any] = {
    "window": {
        "width":       1280,
        "height":       800,
        "minWidth":     800,
        "minHeight":    600,
        "resizable":   True,
        "fullscreen":  False,
        "frame":       True,
    },
    "icon":           None,       # path to source image (png/ico)
    "skipOptimize":   False,      # skip optimizer step
    "devTools":       False,      # open DevTools on launch
    "singleInstance": True,       # prevent multiple app instances
    "autoUpdater":    False,      # future: electron-updater support
    "extraElectronConfig": {},    # merged into BrowserWindow options
}


def load(project_dir: Path) -> dict[str, Any]:
    """
    Load converter config for a project, merging over defaults.
    Returns a fully-resolved config dict.
    """
    config = _deep_copy(DEFAULTS)

    cfg_path = project_dir / CONFIG_FILENAME
    if cfg_path.exists():
        try:
            user_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            _deep_merge(config, user_cfg)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid {CONFIG_FILENAME}: {e}") from e

    return config


def save_example(project_dir: Path):
    """Write an example converter.config.json to the project directory."""
    example = {
        "$schema": "https://besttean.dev/converter-config-schema.json",
        "window": {
            "width":   1280,
            "height":   800,
        },
        "icon":         None,
        "skipOptimize": False,
        "devTools":     False,
    }
    out = project_dir / CONFIG_FILENAME
    out.write_text(json.dumps(example, indent=2), encoding="utf-8")
    return out


def _deep_copy(d: dict) -> dict:
    import copy
    return copy.deepcopy(d)


def _deep_merge(base: dict, override: dict):
    """Recursively merge override into base in-place."""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ── CLI: dump effective config for a project ──────────────────────────────────
if __name__ == "__main__":
    import sys
    proj = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    cfg  = load(proj)
    print(json.dumps(cfg, indent=2))
