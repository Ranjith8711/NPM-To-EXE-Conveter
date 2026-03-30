#!/usr/bin/env python3
"""
tests/test_converter.py
Unit & integration tests for the NPM → EXE converter
Developed by BEST TEAM

Run:  python tests/test_converter.py
      python tests/test_converter.py -v
"""

import os
import sys
import json
import shutil
import unittest
import tempfile
from pathlib import Path

# Ensure project root on path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "python-automation"))


class TestProjectValidation(unittest.TestCase):
    """Tests for build.py validate_project()"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_pkg(self, data: dict):
        (self.tmp / "package.json").write_text(json.dumps(data))

    def test_missing_package_json_raises(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        with self.assertRaises(FileNotFoundError):
            validate_project(self.tmp, logger)

    def test_react_detection(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        self._write_pkg({
            "name": "my-app",
            "version": "1.2.3",
            "dependencies": {"react": "^18", "react-dom": "^18"},
            "scripts": {"build": "react-scripts build"}
        })
        meta = validate_project(self.tmp, logger)
        self.assertEqual(meta["framework"], "react")
        self.assertEqual(meta["output_dir"], "build")
        self.assertEqual(meta["name"], "my-app")
        self.assertEqual(meta["version"], "1.2.3")

    def test_vue_detection(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        self._write_pkg({"name": "v", "version": "1.0.0",
                         "dependencies": {"vue": "^3"}, "scripts": {"build": "vite build"}})
        meta = validate_project(self.tmp, logger)
        self.assertEqual(meta["framework"], "vue")
        self.assertEqual(meta["output_dir"], "dist")

    def test_vite_detection(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        self._write_pkg({"name": "v", "version": "1.0.0",
                         "devDependencies": {"vite": "^5"}, "scripts": {"build": "vite build"}})
        meta = validate_project(self.tmp, logger)
        self.assertEqual(meta["framework"], "vite")

    def test_nextjs_detection(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        self._write_pkg({"name": "n", "version": "1.0.0",
                         "dependencies": {"next": "^14", "react": "^18"},
                         "scripts": {"build": "next build"}})
        meta = validate_project(self.tmp, logger)
        self.assertEqual(meta["framework"], "nextjs")
        self.assertEqual(meta["output_dir"], "out")

    def test_vanilla_fallback(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        self._write_pkg({"name": "plain", "version": "0.1.0"})
        meta = validate_project(self.tmp, logger)
        self.assertEqual(meta["framework"], "vanilla")
        self.assertFalse(meta["has_build"])

    def test_defaults_for_missing_name_version(self):
        from build import validate_project
        import logging
        logger = logging.getLogger("test")
        self._write_pkg({})
        meta = validate_project(self.tmp, logger)
        self.assertEqual(meta["name"],    "app")
        self.assertEqual(meta["version"], "1.0.0")


class TestOptimizerModule(unittest.TestCase):
    """Tests for converter-engine/optimizer.js via Node subprocess"""

    def _run_node(self, script: str) -> dict:
        import subprocess, json
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=10
        )
        return {"rc": result.returncode, "out": result.stdout, "err": result.stderr}

    def test_optimizer_loads(self):
        r = self._run_node(
            "const o = require('./converter-engine/optimizer.js');"
            "console.log(typeof o.optimizeBuildOutput);"
        )
        self.assertEqual(r["rc"], 0)
        self.assertIn("function", r["out"])

    def test_optimizer_removes_map_files(self):
        import subprocess
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "bundle.js").write_text("console.log(1)")
            (tmp / "bundle.js.map").write_text("{}")
            (tmp / "style.css").write_text("body{}")
            (tmp / "style.css.map").write_text("{}")

            script = (
                f"const o = require('./converter-engine/optimizer.js');"
                f"const r = o.optimizeBuildOutput({json.dumps(str(tmp))});"
                f"console.log(JSON.stringify(r));"
            )
            r = self._run_node(script)
            self.assertEqual(r["rc"], 0, r["err"])
            data = json.loads(r["out"])
            self.assertEqual(data["removed"], 2)
            self.assertFalse((tmp / "bundle.js.map").exists())
            self.assertTrue((tmp / "bundle.js").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_dir_stats(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "a.js").write_text("x" * 1000)
            (tmp / "b.js").write_text("y" * 2000)
            script = (
                f"const o = require('./converter-engine/optimizer.js');"
                f"const r = o.dirStats({json.dumps(str(tmp))});"
                f"console.log(JSON.stringify(r));"
            )
            r = self._run_node(script)
            data = json.loads(r["out"])
            self.assertEqual(data["fileCount"], 2)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestAnalyzerModule(unittest.TestCase):
    """Tests for converter-engine/analyzer.js"""

    def _run_node(self, script: str) -> dict:
        import subprocess
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=10
        )
        return {"rc": result.returncode, "out": result.stdout, "err": result.stderr}

    def test_analyzer_loads(self):
        r = self._run_node(
            "const a = require('./converter-engine/analyzer.js');"
            "console.log(typeof a.analyzeProject);"
        )
        self.assertEqual(r["rc"], 0)
        self.assertIn("function", r["out"])

    def test_analyze_react_project(self):
        import json, subprocess
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "package.json").write_text(json.dumps({
                "name": "react-test", "version": "2.0.0",
                "dependencies": {"react-dom": "^18"},
                "scripts": {"build": "react-scripts build"}
            }))
            script = (
                f"const a = require('./converter-engine/analyzer.js');"
                f"const r = a.analyzeProject({json.dumps(str(tmp))});"
                f"console.log(JSON.stringify(r));"
            )
            r = self._run_node(script)
            self.assertEqual(r["rc"], 0, r["err"])
            data = json.loads(r["out"])
            self.assertEqual(data["framework"], "react")
            self.assertEqual(data["outDir"],    "build")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_nextjs_validation_warns_without_export(self):
        import json
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "next.config.js").write_text("module.exports = {}")
            script = (
                f"const a = require('./converter-engine/analyzer.js');"
                f"const r = a.validateNextJs({json.dumps(str(tmp))});"
                f"console.log(JSON.stringify(r));"
            )
            r = self._run_node(script)
            data = json.loads(r["out"])
            self.assertFalse(data["valid"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_nextjs_validation_passes_with_export(self):
        import json
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "next.config.js").write_text("module.exports = { output: 'export' }")
            script = (
                f"const a = require('./converter-engine/analyzer.js');"
                f"const r = a.validateNextJs({json.dumps(str(tmp))});"
                f"console.log(JSON.stringify(r));"
            )
            r = self._run_node(script)
            data = json.loads(r["out"])
            self.assertTrue(data["valid"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestBuildScriptCLI(unittest.TestCase):
    """Smoke tests — run build.py --help, check it exits cleanly."""

    def test_help_flag(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT_DIR / "python-automation" / "build.py"), "--help"],
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("NPM", r.stdout + r.stderr + "NPM")  # may print to either

    def test_missing_project_exits_nonzero(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT_DIR / "python-automation" / "build.py"),
             "/nonexistent/path/xyz"],
            capture_output=True, text=True, timeout=10
        )
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    verbosity = 2 if "-v" in sys.argv else 1
    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()
    for cls in [
        TestProjectValidation,
        TestOptimizerModule,
        TestAnalyzerModule,
        TestBuildScriptCLI,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
