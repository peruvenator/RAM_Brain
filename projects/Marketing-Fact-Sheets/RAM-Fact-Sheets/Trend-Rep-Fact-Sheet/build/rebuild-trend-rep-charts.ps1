# rebuild-trend-rep-charts.ps1
# Monthly automation: rebuild data in data/trend-rep-charts.xlsx on the 3rd business day of each month.
# The Python script is self-gated (--gate-business-day 3) -- if today is not the 3rd business day it exits 0.
# On actual failure, this wrapper sends a Slack alert and (if available) logs a Notion run record.

$ErrorActionPreference = "Stop"

# -- Paths --
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir  = Resolve-Path (Join-Path $ScriptDir "..") | Select-Object -ExpandProperty Path
$RepoRoot    = Resolve-Path (Join-Path $ScriptDir "..\..\..\..\..") | Select-Object -ExpandProperty Path
$BuildScript = Join-Path $ScriptDir "build_benchmarks.py"
$OutputXlsx  = Join-Path $ProjectDir "data\trend-rep-charts.xlsx"

# -- Load .env (root) --
$envFile = Join-Path $RepoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
        }
    }
}

# -- Logging --
$LogDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile   = Join-Path $LogDir "rebuild_$timestamp.log"

function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $entry
    $entry | Out-File -FilePath $logFile -Append -Encoding utf8
}

# -- Shared helpers (Slack, Notion run logging) --
$helpersPath = Join-Path $RepoRoot "projects\weekly-scorecard\automation-helpers.ps1"
if (Test-Path $helpersPath) {
    . $helpersPath
} else {
    Write-Log "WARNING: automation-helpers.ps1 not found at $helpersPath -- Slack/Notion alerting disabled"
}

Write-Log "===== Trend Rep Charts Rebuild ====="
Write-Log "Repo root:    $RepoRoot"
Write-Log "Project dir:  $ProjectDir"
Write-Log "Build script: $BuildScript"
Write-Log "Output xlsx:  $OutputXlsx"

if (-not (Test-Path $BuildScript)) {
    $msg = "Build script not found: $BuildScript"
    Write-Log $msg
    if (Get-Command Send-SlackAlert -ErrorAction SilentlyContinue) {
        Send-SlackAlert -Message ":warning: *Trend Rep Charts Rebuild* failed: $msg"
    }
    exit 1
}

# -- Run Python with 3rd-business-day gate --
try {
    Write-Log "Running: python $BuildScript --gate-business-day 3"
    $output = & python $BuildScript --gate-business-day 3 2>&1
    $output | ForEach-Object { Write-Log "  $_" }

    if ($LASTEXITCODE -ne 0) {
        throw "build_benchmarks.py exited with code $LASTEXITCODE"
    }

    $skipped = $false
    foreach ($line in $output) {
        if ($line -match '^\[skip\]') { $skipped = $true; break }
    }

    if ($skipped) {
        Write-Log "Run skipped by date/data gate. No rebuild performed."
        if (Get-Command Log-NotionRun -ErrorAction SilentlyContinue) {
            Log-NotionRun -AutomationName "Trend Rep Charts Rebuild" -OverallStatus "Skipped" -Details "Not the 3rd business day of the month"
        }
        exit 0
    }

    if (-not (Test-Path $OutputXlsx)) {
        throw "Output xlsx was not created: $OutputXlsx"
    }

    $xlsxSize = (Get-Item $OutputXlsx).Length
    Write-Log "Rebuild complete. Output size: $([math]::Round($xlsxSize / 1KB, 1)) KB"

    if (Get-Command Log-NotionRun -ErrorAction SilentlyContinue) {
        Log-NotionRun -AutomationName "Trend Rep Charts Rebuild" -OverallStatus "Success" -Details "Output: $([math]::Round($xlsxSize / 1KB, 1)) KB"
    }
}
catch {
    $errMsg = "Rebuild FAILED: $_"
    Write-Log $errMsg

    if (Get-Command Log-NotionRun -ErrorAction SilentlyContinue) {
        Log-NotionRun -AutomationName "Trend Rep Charts Rebuild" -OverallStatus "Failed" -Details $errMsg
    }
    if (Get-Command Send-SlackAlert -ErrorAction SilentlyContinue) {
        $logName = Split-Path $logFile -Leaf
        Send-SlackAlert -Message ":warning: *Trend Rep Charts Rebuild* failed at $(Get-Date -Format 'yyyy-MM-dd HH:mm')`n$errMsg`nLog: $logName"
    }
    exit 1
}

Write-Log "===== Done ====="

# -- Log cleanup: delete logs older than 180 days --
Get-ChildItem -Path $LogDir -Filter "rebuild_*.log" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-180) } |
    Remove-Item -Force
