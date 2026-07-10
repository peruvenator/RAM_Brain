@echo off
REM run-source-file-sync.bat
REM Launcher for Windows Task Scheduler.
REM Runs the PowerShell wrapper which handles logging and alerting.

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0run-source-file-sync.ps1"
