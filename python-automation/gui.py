#!/usr/bin/env python3
"""
NPM → EXE Converter — GUI Launcher
Developed by BEST TEAM
A tkinter-based graphical interface for the build pipeline.
"""

import os
import sys
import json
import time
import threading
import subprocess
import platform
from pathlib import Path
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("tkinter not available. Use the CLI: python python-automation/build.py")
    sys.exit(1)

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_PY = ROOT_DIR / "python-automation" / "build.py"

# ─── Color palette ────────────────────────────────────────────────────────────
BG        = "#0d0d14"
SURFACE   = "#13131f"
BORDER    = "#1e1e35"
ACCENT    = "#5b5ef5"
ACCENT2   = "#00e5c0"
TEXT      = "#e8e8f5"
DIM       = "#5a5a80"
SUCCESS   = "#00e5c0"
ERROR     = "#ff4d6d"
WARN      = "#ffd166"
MONO      = "Courier New" if platform.system() == "Windows" else "Courier"


class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("NPM → EXE Converter  |  BEST TEAM")
        self.geometry("820x680")
        self.minsize(700, 560)
        self.configure(bg=BG)

        # State
        self.project_path = tk.StringVar(value=str(ROOT_DIR / "input-project"))
        self.skip_build   = tk.BooleanVar(value=False)
        self.running      = False
        self.proc         = None

        self._build_ui()
        self._check_prereqs_async()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="NPM Project  →  Windows EXE",
                 font=("Arial", 16, "bold"), fg=TEXT, bg=SURFACE).pack()
        tk.Label(hdr, text="Developed by BEST TEAM",
                 font=("Arial", 9), fg=DIM, bg=SURFACE).pack()

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Main body
        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        # ── Project path row ──────────────────────────────────────────────────
        tk.Label(body, text="PROJECT PATH", font=("Arial", 8, "bold"),
                 fg=DIM, bg=BG).pack(anchor="w")

        path_row = tk.Frame(body, bg=BG)
        path_row.pack(fill="x", pady=(4, 12))

        path_entry = tk.Entry(path_row, textvariable=self.project_path,
                              bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                              relief="flat", bd=6, font=(MONO, 10))
        path_entry.pack(side="left", fill="x", expand=True)

        tk.Button(path_row, text="Browse…", command=self._browse,
                  bg=BORDER, fg=TEXT, relief="flat", padx=10, cursor="hand2"
                  ).pack(side="left", padx=(8, 0))

        # ── Options row ───────────────────────────────────────────────────────
        opts = tk.Frame(body, bg=BG)
        opts.pack(fill="x", pady=(0, 12))
        tk.Checkbutton(opts, text="Skip web build  (already built)",
                       variable=self.skip_build,
                       bg=BG, fg=DIM, selectcolor=SURFACE,
                       activebackground=BG, activeforeground=TEXT
                       ).pack(side="left")

        # ── Prerequisites panel ───────────────────────────────────────────────
        tk.Label(body, text="PREREQUISITES", font=("Arial", 8, "bold"),
                 fg=DIM, bg=BG).pack(anchor="w")

        prereq_frame = tk.Frame(body, bg=SURFACE, pady=8, padx=10)
        prereq_frame.pack(fill="x", pady=(4, 12))

        self.prereq_labels = {}
        for tool in ["Python", "Node.js", "npm"]:
            row = tk.Frame(prereq_frame, bg=SURFACE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{tool}:", width=10, anchor="w",
                     fg=DIM, bg=SURFACE, font=("Arial", 9)).pack(side="left")
            lbl = tk.Label(row, text="checking…", fg=WARN, bg=SURFACE,
                           font=(MONO, 9))
            lbl.pack(side="left")
            self.prereq_labels[tool] = lbl

        # ── Pipeline progress ─────────────────────────────────────────────────
        tk.Label(body, text="PIPELINE", font=("Arial", 8, "bold"),
                 fg=DIM, bg=BG).pack(anchor="w", pady=(0, 4))

        stages = [
            "Validate Project",
            "Install Dependencies",
            "Build Web Project",
            "Prepare Electron",
            "Install Electron Deps",
            "Package EXE",
            "Verify Output",
        ]
        pipe_frame = tk.Frame(body, bg=BG)
        pipe_frame.pack(fill="x", pady=(0, 12))

        self.stage_labels = []
        for i, s in enumerate(stages):
            col = tk.Frame(pipe_frame, bg=BORDER, padx=1, pady=1)
            col.pack(side="left", fill="x", expand=True, padx=(0, 1))
            inner = tk.Frame(col, bg=SURFACE, pady=6)
            inner.pack(fill="both")
            tk.Label(inner, text=f"{i+1}", font=("Arial", 7), fg=DIM, bg=SURFACE).pack()
            lbl = tk.Label(inner, text=s, font=("Arial", 7), fg=DIM,
                           bg=SURFACE, wraplength=80, justify="center")
            lbl.pack()
            self.stage_labels.append(lbl)

        # ── Log output ────────────────────────────────────────────────────────
        tk.Label(body, text="BUILD LOG", font=("Arial", 8, "bold"),
                 fg=DIM, bg=BG).pack(anchor="w")

        self.log = scrolledtext.ScrolledText(
            body, height=12, bg="#0a0a10", fg=TEXT,
            font=(MONO, 9), relief="flat", bd=0,
            insertbackground=TEXT, state="disabled"
        )
        self.log.pack(fill="both", expand=True, pady=(4, 12))

        # Tag colours for log
        self.log.tag_config("ok",    foreground=SUCCESS)
        self.log.tag_config("err",   foreground=ERROR)
        self.log.tag_config("warn",  foreground=WARN)
        self.log.tag_config("info",  foreground=DIM)
        self.log.tag_config("bold",  foreground=TEXT, font=(MONO, 9, "bold"))
        self.log.tag_config("accent",foreground=ACCENT)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x")

        self.run_btn = tk.Button(
            btn_row, text="▶  START BUILD",
            command=self._start_build,
            bg=ACCENT, fg="white", relief="flat",
            font=("Arial", 11, "bold"), padx=20, pady=8,
            cursor="hand2", activebackground="#4a4de0", activeforeground="white"
        )
        self.run_btn.pack(side="left")

        self.stop_btn = tk.Button(
            btn_row, text="■  STOP",
            command=self._stop_build,
            bg=BORDER, fg=ERROR, relief="flat",
            font=("Arial", 10), padx=14, pady=8,
            cursor="hand2", state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        tk.Button(btn_row, text="Open Output Folder",
                  command=self._open_output,
                  bg=BORDER, fg=DIM, relief="flat",
                  padx=10, pady=8, cursor="hand2"
                  ).pack(side="right")

        tk.Button(btn_row, text="Clear Log",
                  command=self._clear_log,
                  bg=BORDER, fg=DIM, relief="flat",
                  padx=10, pady=8, cursor="hand2"
                  ).pack(side="right", padx=(0, 6))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self, textvariable=self.status_var,
                              bg=SURFACE, fg=DIM, anchor="w", padx=12, pady=4)
        status_bar.pack(fill="x", side="bottom")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory(title="Select your NPM project folder")
        if d:
            self.project_path.set(d)

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _open_output(self):
        out = ROOT_DIR / "output"
        out.mkdir(exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(str(out))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(out)])
        else:
            subprocess.Popen(["xdg-open", str(out)])

    def _log(self, msg: str, tag: str = ""):
        self.log.configure(state="normal")
        # Strip ANSI codes
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', msg)
        self.log.insert("end", clean + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _set_stage(self, index: int, state: str):
        """state: idle | running | done | error"""
        colors = {
            "idle":    (SURFACE, DIM),
            "running": ("#1a1a35", ACCENT),
            "done":    ("#0d2020", SUCCESS),
            "error":   ("#200d0d", ERROR),
        }
        bg, fg = colors.get(state, (SURFACE, DIM))
        lbl = self.stage_labels[index]
        lbl.configure(fg=fg, bg=bg)
        lbl.master.configure(bg=bg)

    def _reset_stages(self):
        for i in range(7):
            self._set_stage(i, "idle")

    # ── Prereq check ──────────────────────────────────────────────────────────
    def _check_prereqs_async(self):
        threading.Thread(target=self._check_prereqs, daemon=True).start()

    def _check_prereqs(self):
        checks = {
            "Python":  ["python", "--version"],
            "Node.js": ["node", "--version"],
            "npm":     ["npm",   "--version"],
        }
        # On Windows npm is npm.cmd
        if platform.system() == "Windows":
            checks["npm"] = ["npm.cmd", "--version"]

        for tool, cmd in checks.items():
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                version = r.stdout.strip() or r.stderr.strip()
                self.after(0, lambda t=tool, v=version: self._set_prereq(t, v, True))
            except Exception as e:
                self.after(0, lambda t=tool, e=str(e): self._set_prereq(t, "NOT FOUND", False))

    def _set_prereq(self, tool: str, text: str, ok: bool):
        lbl = self.prereq_labels[tool]
        lbl.configure(text=text, fg=SUCCESS if ok else ERROR)

    # ── Build ─────────────────────────────────────────────────────────────────
    def _start_build(self):
        if self.running:
            return

        proj = self.project_path.get().strip()
        if not proj or not Path(proj).exists():
            messagebox.showerror("Error", f"Project path not found:\n{proj}")
            return

        pkg = Path(proj) / "package.json"
        if not pkg.exists():
            messagebox.showerror("Error", f"No package.json found in:\n{proj}")
            return

        self.running = True
        self.run_btn.configure(state="disabled", bg=DIM)
        self.stop_btn.configure(state="normal")
        self._reset_stages()
        self._clear_log()
        self._log("━" * 60, "info")
        self._log(f"  Build started  {datetime.now().strftime('%H:%M:%S')}", "bold")
        self._log("━" * 60, "info")

        threading.Thread(target=self._run_build, args=(proj,), daemon=True).start()

    def _stop_build(self):
        if self.proc:
            self.proc.terminate()
        self._finish_build(cancelled=True)

    def _run_build(self, proj: str):
        python = sys.executable
        cmd = [python, str(BUILD_PY), proj]
        if self.skip_build.get():
            cmd.append("--skip-web-build")

        stage_keywords = [
            "Validating project",
            "Installing project dependencies",
            "Building web project",
            "Preparing Electron",
            "Installing Electron dependencies",
            "Packaging Windows EXE",
            "Verifying output",
        ]
        current_stage = -1

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            for line in self.proc.stdout:
                line = line.rstrip()
                if not line:
                    continue

                # Detect stage transitions
                for i, kw in enumerate(stage_keywords):
                    if kw.lower() in line.lower() and i > current_stage:
                        if current_stage >= 0:
                            self.after(0, lambda s=current_stage: self._set_stage(s, "done"))
                        current_stage = i
                        self.after(0, lambda s=i: self._set_stage(s, "running"))
                        break

                # Pick log tag
                tag = "info"
                low = line.lower()
                if "✔" in line or "success" in low:
                    tag = "ok"
                elif "✖" in line or "error" in low or "failed" in low:
                    tag = "err"
                elif "⚠" in line or "warn" in low:
                    tag = "warn"
                elif line.strip().startswith("["):
                    tag = "bold"

                self.after(0, lambda l=line, t=tag: self._log(l, t))

            self.proc.wait()
            success = self.proc.returncode == 0

            if current_stage >= 0:
                self.after(0, lambda s=current_stage, ok=success:
                           self._set_stage(s, "done" if ok else "error"))

            self.after(0, lambda: self._finish_build(success=success))

        except Exception as exc:
            self.after(0, lambda e=str(exc): self._log(f"\n  Error: {e}", "err"))
            self.after(0, lambda: self._finish_build(success=False))

    def _finish_build(self, success: bool = False, cancelled: bool = False):
        self.running = False
        self.proc    = None
        self.run_btn.configure(state="normal", bg=ACCENT)
        self.stop_btn.configure(state="disabled")

        if cancelled:
            self._log("\n  Build cancelled.", "warn")
            self._set_status("Cancelled")
        elif success:
            self._log("\n  ✔  Build successful! EXE is in output/", "ok")
            self._set_status("✔  Build complete — check output/")
        else:
            self._log("\n  ✖  Build failed. See log above or check logs/ folder.", "err")
            self._set_status("✖  Build failed — check logs/")


def main():
    app = ConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
