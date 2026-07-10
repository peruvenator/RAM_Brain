@echo off
REM Thin wrapper for Windows Task Scheduler -- weekly calendar briefing (Sunday 8 PM ET).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\daily-briefing\run-briefing.ps1" -Mode weekly
