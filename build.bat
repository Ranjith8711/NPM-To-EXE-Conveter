@echo off
title NPM to EXE Converter
color 0A
cd /d "%~dp0"

echo.
echo  ============================================================
echo   NPM PROJECT to WINDOWS .EXE CONVERTER
echo   Production Build Engine v1.0
echo   Developed By Ranjith R
echo  ============================================================
echo.
echo  Root folder: %CD%
echo.

:: ── Tool checks using WHERE (never corrupts errorlevel) ──────────
where python >nul 2>&1
if %errorlevel% NEQ 0 (
    color 0C
    echo  [ERROR] Python not found!
    echo  Install from: https://python.org/downloads
    echo  TICK "Add Python to PATH" then restart your PC.
    echo.
    pause
    exit /b 1
)
echo  [OK] Python found

where node >nul 2>&1
if %errorlevel% NEQ 0 (
    color 0C
    echo  [ERROR] Node.js not found!
    echo  Install from: https://nodejs.org/en/download
    echo  Keep all defaults, then restart your PC.
    echo.
    pause
    exit /b 1
)
echo  [OK] Node.js found

where npm >nul 2>&1
if %errorlevel% NEQ 0 (
    color 0C
    echo  [ERROR] NPM not found. Reinstall Node.js from https://nodejs.org
    echo.
    pause
    exit /b 1
)
echo  [OK] NPM found

echo.

:: ── Check for project ────────────────────────────────────────────
if not exist "input-project\package.json" (
    color 0E
    echo  [WARN] No package.json in input-project\
    echo.
    echo  Copy your NPM project into input-project\ and run again.
    echo  Or use START HERE.bat which has a guided setup.
    echo.
    pause
    exit /b 1
)

:: ── Run build ────────────────────────────────────────────────────
echo  [....] Starting build pipeline...
echo.

python python-automation\build.py %*
set BUILD_RESULT=%errorlevel%

echo.
if %BUILD_RESULT% NEQ 0 (
    color 0C
    echo  BUILD FAILED. Check logs\ folder for details.
    echo.
) else (
    color 0A
    echo  BUILD COMPLETE! EXE is in the output\ folder.
    echo.
    if exist "output" start "" explorer.exe "%CD%\output"
)

pause
