# run-source-file-sync.ps1
# Wrapper for Notion Source File Sync automation.
# Dot-sources shared automation-helpers.ps1 for Notion run logging and Slack alerts.

$ErrorActionPreference = "Stop"

# ── Paths ────────────────────────────────────────────────────────────────────
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$brainRoot  = (Resolve-Path "$scriptDir\..\..").Path
$envFile    = Join-Path $brainRoot ".env"
$logDir     = Join-Path $scriptDir "logs"
$logFile    = Join-Path $logDir ("sync_{0}.log" -f (Get-Date -Format "yyyy-MM-dd_HHmm"))
$pythonScript = Join-Path $scriptDir "notion_source_file_sync.py"

# ── Ensure log directory exists ──────────────────────────────────────────────
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

# ── Write-Log ────────────────────────────────────────────────────────────────
function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$ts] $Message"
    Write-Host $entry
    Add-Content -Path $logFile -Value $entry
}

# ── Load .env ────────────────────────────────────────────────────────────────
$envVars = @{}
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line -split "=", 2
            $envVars[$parts[0].Trim()] = $parts[1].Trim()
        }
    }
}

# ── Config for automation-helpers.ps1 ────────────────────────────────────────
$Config = @{
    NotionToken         = $envVars["NOTION_TOKEN"]
    SlackWebhook        = $envVars["SLACK_WEBHOOK"]
    NotionRunsDbId      = "3023037cb38a815fb09fd3d2b6f71ae7"
    NotionInventoryDbId = "3023037cb38a814bac81cb56a89af346"
}

# ── Dot-source shared helpers ────────────────────────────────────────────────
$helpersPath = Join-Path $brainRoot "projects\weekly-scorecard\automation-helpers.ps1"
if (Test-Path $helpersPath) {
    . $helpersPath
    Write-Log "Loaded automation-helpers.ps1"
} else {
    Write-Log "WARNING: automation-helpers.ps1 not found at $helpersPath"
}

# ── Automation name (must match Notion Automations Inventory entry) ──────────
$automationName = "Source File Sync"

# ── Run the Python script ────────────────────────────────────────────────────
Write-Log "Starting Notion Source File Sync..."
Write-Log "Python script: $pythonScript"

$output = ""
$exitCode = 0

try {
    $output = & python $pythonScript 2>&1 | Tee-Object -FilePath $logFile -Append | Out-String
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Log "Python script completed successfully (exit code 0)"
        Log-NotionRun -AutomationName $automationName -OverallStatus "Success" -Details $output
    } else {
        Write-Log "Python script failed (exit code $exitCode)"
        Log-NotionRun -AutomationName $automationName -OverallStatus "Failure" -Details "Exit code: $exitCode`n$output"
        Send-SlackAlert ":x: *Source File Sync* failed (exit $exitCode). Check log: $logFile"
    }
}
catch {
    $errorMsg = $_.Exception.Message
    Write-Log "EXCEPTION: $errorMsg"
    Log-NotionRun -AutomationName $automationName -OverallStatus "Failure" -Details "Exception: $errorMsg`n$output"
    Send-SlackAlert ":x: *Source File Sync* threw an exception: $errorMsg"
    exit 1
}

exit $exitCode
