@echo off
REM Task Scheduler wrapper for the Cockroach Carry monthly report.
REM Quotes the full PS1 path so spaces in the Dropbox path don't break.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-cockroach-report.ps1"
