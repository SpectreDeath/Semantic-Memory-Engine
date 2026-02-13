@echo off
REM ──────────────────────────────────────────────
REM  SME Brain Agent — Python 3.13 Sidecar Runtime
REM  AionUi ACP shim for auto-detection
REM ──────────────────────────────────────────────
set "PROJECT_ROOT=%~dp0.."
set "VIRTUAL_ENV=%PROJECT_ROOT%\.brain_venv"
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
set "PYTHONPATH=%PROJECT_ROOT%"

"%VIRTUAL_ENV%\Scripts\python.exe" "%PROJECT_ROOT%\src\ai\brain_worker.py" %*
