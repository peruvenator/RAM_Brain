@echo off
REM Batch launcher for rebuild-trend-rep-charts.ps1 (Windows Task Scheduler handles spaced paths poorly).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0rebuild-trend-rep-charts.ps1"
exit /b %ERRORLEVEL%
