@echo off
REM Thin wrapper for Windows Task Scheduler to launch the weekly scorecard automation.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\run-weekly-scorecard.ps1"
