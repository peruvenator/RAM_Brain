#requires -Version 5.1
<#
Installs Meeting Voice for the current Windows user (no admin rights needed):
  1. copies MeetingVoice.ps1 and config.json to %LOCALAPPDATA%\MeetingVoice
  2. signs you in to Microsoft 365 if you have not signed in yet
  3. adds a shortcut to your Startup folder so it runs hidden at every logon
  4. starts it now

  powershell -ExecutionPolicy Bypass -File .\Install-MeetingVoice.ps1
  powershell -ExecutionPolicy Bypass -File .\Install-MeetingVoice.ps1 -Uninstall
#>
[CmdletBinding()]
param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'
$AppDir   = Join-Path $env:LOCALAPPDATA 'MeetingVoice'
$Script   = Join-Path $AppDir 'MeetingVoice.ps1'
$Shortcut = Join-Path ([Environment]::GetFolderPath('Startup')) 'Meeting Voice.lnk'
$PsExe    = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$RunArgs  = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`""

function Stop-Running {
    Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" |
        Where-Object {
            $_.ProcessId -ne $PID -and
            $_.CommandLine -like "*$Script*" -and
            $_.CommandLine -notlike '*-SignIn*'
        } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "Stopped running copy (PID $($_.ProcessId))." }
}

if ($Uninstall) {
    Stop-Running
    if (Test-Path $Shortcut) { Remove-Item $Shortcut; Write-Host 'Removed Startup shortcut.' }
    if (Test-Path $AppDir)   { Remove-Item $AppDir -Recurse -Force; Write-Host "Removed $AppDir (including saved sign-in)." }
    Write-Host 'Meeting Voice is uninstalled.'
    return
}

$cfg = Get-Content (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json
if ("$($cfg.TenantId)$($cfg.ClientId)" -like '*PASTE*' -or -not $cfg.TenantId -or -not $cfg.ClientId) {
    throw 'Fill in TenantId and ClientId in config.json first (see README.md, step 1).'
}

Stop-Running
New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'MeetingVoice.ps1') $AppDir -Force
Copy-Item (Join-Path $PSScriptRoot 'config.json') $AppDir -Force
Write-Host "Copied files to $AppDir"

if (-not (Test-Path (Join-Path $AppDir 'token.dat'))) {
    Write-Host "`nSigning in to Microsoft 365..."
    & $PsExe -NoProfile -ExecutionPolicy Bypass -File $Script -SignIn
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $AppDir 'token.dat'))) { throw 'Sign-in did not complete.' }
}

Write-Host "`nTesting: listing your upcoming meetings and speaking the next one..."
& $PsExe -NoProfile -ExecutionPolicy Bypass -File $Script -Test
if ($LASTEXITCODE -ne 0) { throw 'Test failed; see the error above.' }

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($Shortcut)
$lnk.TargetPath = $PsExe
$lnk.Arguments = $RunArgs
$lnk.WorkingDirectory = $AppDir
$lnk.WindowStyle = 7   # minimized
$lnk.Description = 'Speaks upcoming Microsoft 365 meetings'
$lnk.Save()
Write-Host "`nAdded Startup shortcut: $Shortcut"

Start-Process -FilePath $PsExe -ArgumentList $RunArgs -WindowStyle Hidden
Write-Host 'Meeting Voice is running in the background.'
Write-Host "Log file: $(Join-Path $AppDir 'log.txt')"
