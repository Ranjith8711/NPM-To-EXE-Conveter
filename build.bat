@echo off
setlocal EnableDelayedExpansion

title NPM to EXE Converter — BEST TEAM

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║          NPM Project ^→ Windows EXE Converter               ║
echo  ║                   Developed by BEST TEAM                   ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

REM ── Check Python ──────────────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    where python3 >nul 2>&1
    if errorlevel 1 (
        echo  [ERROR] Python not found. Install from https://python.org
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

REM ── Check Node.js ─────────────────────────────────────────────────────────────
where node >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)

REM ── Check npm ─────────────────────────────────────────────────────────────────
where npm >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] npm not found. Reinstall Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo  [OK] Python: & %PYTHON% --version
echo  [OK] Node:   & node --version
echo  [OK] npm:    & npm --version
echo.

REM ── Check input-project ───────────────────────────────────────────────────────
if not exist "input-project\package.json" (
    echo  [WARN] No project found in input-project\
    echo         Copy your NPM project there or pass a path:
    echo         python python-automation\build.py C:\path\to\your\project
    echo.
    pause
    exit /b 1
)

REM ── Run build ─────────────────────────────────────────────────────────────────
echo  Starting build pipeline...
echo.
%PYTHON% python-automation\build.py %*

if errorlevel 1 (
    echo.
    echo  [FAILED] Build failed. Check logs\ for details.
    pause
    exit /b 1
)

echo.
echo  [DONE] Your EXE is in the output\ folder!
pause
