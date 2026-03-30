@echo off
title NPM → EXE Converter GUI — BEST TEAM

where python >nul 2>&1
if errorlevel 1 (
    where python3 >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found. Install from https://python.org
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

%PYTHON% python-automation\gui.py
