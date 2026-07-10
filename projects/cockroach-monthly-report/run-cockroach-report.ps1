# run-cockroach-report.ps1
# Monthly Cockroach Carry performance report -> Slack.
# Thin wrapper: loads .env, runs generate_report.py, logs output, alerts Slack on failure.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── Logging ──────────────────────────────────────────────────────────────────
$LogDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile   = Join-Path $LogDir "cockroach_$timestamp.log"

function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $entry
    $entry | Out-File -FilePath $logFile -Append -Encoding utf8
}

# ── Load .env (project first, then repo root) for the failure-alert webhook ───
$envFiles = @(
    (Join-Path $ScriptDir ".env"),
    (Join-Path (Split-Path -Parent (Split-Path -Parent $ScriptDir)) ".env")
)
foreach ($envFile in $envFiles) {
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)$') {
                $k = $Matches[1].Trim()
                if (-not [Environment]::GetEnvironmentVariable($k, "Process")) {
                    [Environment]::SetEnvironmentVariable($k, $Matches[2].Trim(), "Process")
                }
            }
        }
    }
}

function Send-SlackAlert {
    param([string]$Message)
    $webhook = [Environment]::GetEnvironmentVariable("SLACK_WEBHOOK", "Process")
    if (-not $webhook) { Write-Log "No SLACK_WEBHOOK -- cannot send alert"; return }
    try {
        $body = @{ text = $Message } | ConvertTo-Json
        Invoke-RestMethod -Uri $webhook -Method POST -Body $body -ContentType "application/json" | Out-Null
    } catch {
        Write-Log "Slack alert failed: $_"
    }
}

# ── Run ──────────────────────────────────────────────────────────────────────
Write-Log "===== Cockroach Carry Monthly Report started ====="
Write-Log "Script dir: $ScriptDir"

try {
    $py = Join-Path $ScriptDir "generate_report.py"
    Write-Log "Running: python `"$py`""
    $output = & python $py 2>&1
    $exit = $LASTEXITCODE
    $output | ForEach-Object { Write-Log $_ }

    if ($exit -ne 0) {
        throw "generate_report.py exited with code $exit"
    }
    Write-Log "===== Run complete (success) ====="
}
catch {
    Write-Log "FAILED: $_"
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm"
    $logName = Split-Path $logFile -Leaf
    Send-SlackAlert -Message ":warning: *Cockroach Carry Monthly Report* failed at $ts`n$_`nLog: $logName"
    exit 1
}

# ── Log cleanup: delete logs older than 180 days ─────────────────────────────
Get-ChildItem -Path $LogDir -Filter "cockroach_*.log" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-180) } |
    Remove-Item -Force
