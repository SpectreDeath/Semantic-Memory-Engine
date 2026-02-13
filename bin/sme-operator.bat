@echo off
REM ──────────────────────────────────────────────
REM  SME Operator Agent — Python 3.14 Main Runtime
REM  AionUi ACP shim for auto-detection
REM ──────────────────────────────────────────────
set "PROJECT_ROOT=%~dp0.."
set "VIRTUAL_ENV=%PROJECT_ROOT%\.venv"
set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
set "PYTHONPATH=%PROJECT_ROOT%"

"%VIRTUAL_ENV%\Scripts\python.exe" -m sme_cli %*
