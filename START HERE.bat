@echo off
title NPM to EXE Converter
color 0A
cd /d "%~dp0"

echo.
echo  ============================================================
echo   NPM PROJECT to WINDOWS .EXE CONVERTER
echo   Developed By Ranjith R
echo  ============================================================
echo.
echo  Root folder: %CD%
echo.

:: ── Use WHERE to check tools - never corrupts errorlevel ─────────
where python >nul 2>&1
if %errorlevel% NEQ 0 (
    color 0C
    echo  [ERROR] Python not found!
    echo.
    echo  1. Download from: https://python.org/downloads
    echo  2. Run the installer
    echo  3. TICK "Add Python to PATH" checkbox
    echo  4. Restart your PC then run this again
    echo.
    pause
    exit /b 1
)
echo  [OK] Python found

where node >nul 2>&1
if %errorlevel% NEQ 0 (
    color 0C
    echo  [ERROR] Node.js not found!
    echo.
    echo  1. Download LTS from: https://nodejs.org/en/download
    echo  2. Run installer, keep all defaults
    echo  3. Restart your PC then run this again
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

:: ── Check for project in input-project\ ──────────────────────────
if exist "input-project\package.json" (
    echo  [OK] Project found in input-project\
    goto :run_build
)

:: No project — show options
color 0E
echo  ============================================================
echo   NO PROJECT FOUND IN input-project\
echo  ============================================================
echo.
echo  TO CONVERT YOUR OWN PROJECT:
echo    1. Open the  input-project\  folder (inside this folder)
echo    2. Copy ALL your NPM project files into it
echo       package.json must be directly inside input-project\
echo    3. Run this script again
echo.

if not exist "demo-app\package.json" (
    echo  Add your project to input-project\ and run again.
    echo.
    pause
    exit /b 0
)

echo  ============================================================
echo  OR press Y to test with the built-in demo app right now.
echo.
choice /C YN /M "  Test with demo app now?"
if %errorlevel% EQU 2 (
    echo.
    echo  OK. Put your project in input-project\ and run again.
    echo.
    pause
    exit /b 0
)

:: Copy demo app into input-project\
color 0A
echo.
echo  Copying demo app to input-project\...
if not exist "input-project" mkdir "input-project"
xcopy /E /I /Y "demo-app\*" "input-project\" >nul
echo  [OK] Demo app is ready.
echo.

:run_build
color 0A
echo  ============================================================
echo   STARTING BUILD PIPELINE
echo  ============================================================
echo.

python python-automation\build.py %*
set BUILD_RESULT=%errorlevel%

echo.
if %BUILD_RESULT% NEQ 0 (
    color 0C
    echo  ============================================================
    echo   BUILD FAILED
    echo  ============================================================
    echo.
    echo  Check the  logs\  folder for full details.
    echo  Also try:  python python-automation\validate.py
    echo.
) else (
    color 0A
    echo  ============================================================
    echo   BUILD COMPLETE! EXE is in the output\ folder.
    echo  ============================================================
    echo.
    if exist "output" start "" explorer.exe "%CD%\output"
)

pause
