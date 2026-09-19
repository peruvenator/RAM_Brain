@echo off
REM Launches a dedicated Chrome profile that the FINTRX SDK is allowed to
REM eavesdrop on (Chrome 136+ refuses remote debugging on normal profiles).
REM First run: log into platform.fintrx.com once. The profile stays logged in.
REM Profile lives outside Dropbox at %USERPROFILE%\.fintrx-chrome
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%USERPROFILE%\.fintrx-chrome" ^
  --no-first-run --no-default-browser-check ^
  https://platform.fintrx.com
