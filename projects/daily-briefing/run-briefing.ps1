param(
    [ValidateSet("daily", "weekly")]
    [string]$Mode = "daily"
)

# ============================================================
# Calendar Briefing Automation
# Sends a Slack message with upcoming calendar events.
#   -Mode daily  : tomorrow's schedule (runs nightly at 8 PM)
#   -Mode weekly : Mon-Fri next week (runs Sunday at 8 PM)
# Filters out "Deep Work Block" entries.
# ============================================================

# --- Load .env ---
$envFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)$') {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
}

# --- Validate required vars ---
$requiredVars = @(
    "MS365_CLIENT_ID", "MS365_TENANT_ID", "MS365_CLIENT_SECRET",
    "MS365_USER_EMAIL", "SLACK_WEBHOOK",
    "NOTION_TOKEN", "NOTION_RUNS_DB_ID", "NOTION_INVENTORY_DB_ID"
)
foreach ($var in $requiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        Write-Error "Missing required .env variable: $var"
        exit 1
    }
}

# --- Build config (shared helpers expect $Config) ---
$Config = @{
    ClientId            = $env:MS365_CLIENT_ID
    TenantId            = $env:MS365_TENANT_ID
    ClientSecret        = $env:MS365_CLIENT_SECRET
    UserEmail           = $env:MS365_USER_EMAIL
    SlackWebhook        = $env:SLACK_WEBHOOK
    NotionToken         = $env:NOTION_TOKEN
    NotionRunsDbId      = $env:NOTION_RUNS_DB_ID
    NotionInventoryDbId = $env:NOTION_INVENTORY_DB_ID
}

# --- Setup logging ---
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }
$logFile = Join-Path $logsDir ("briefing-$Mode-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")

function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $entry
    $entry | Out-File -FilePath $logFile -Append -Encoding utf8
}

# --- Dot-source shared helpers ---
. "$PSScriptRoot\..\weekly-scorecard\automation-helpers.ps1"

# ============================================================
# Microsoft Graph API
# ============================================================

function Get-GraphToken {
    $tokenUrl = "https://login.microsoftonline.com/$($Config.TenantId)/oauth2/v2.0/token"
    $body = @{
        client_id     = $Config.ClientId
        client_secret = $Config.ClientSecret
        scope         = "https://graph.microsoft.com/.default"
        grant_type    = "client_credentials"
    }
    $response = Invoke-RestMethod -Uri $tokenUrl -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
    return $response.access_token
}

function Get-CalendarEvents {
    param(
        [string]$Token,
        [datetime]$StartDate,
        [datetime]$EndDate
    )
    $start = $StartDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
    $end   = $EndDate.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
    $url   = "https://graph.microsoft.com/v1.0/users/$($Config.UserEmail)/calendarView?startDateTime=$start&endDateTime=$end&`$orderby=start/dateTime&`$top=50"
    $headers = @{
        Authorization = "Bearer $Token"
        Prefer        = 'outlook.timezone="Eastern Standard Time"'
    }
    $response = Invoke-RestMethod -Uri $url -Method GET -Headers $headers
    return $response.value
}

# ============================================================
# Determine date range
# ============================================================

$now = Get-Date

if ($Mode -eq "daily") {
    $tomorrow   = $now.AddDays(1).Date
    $startDate  = $tomorrow
    $endDate    = $tomorrow.AddDays(1)
    $automationName = "Daily Briefing"
}
else {
    # Weekly: next Monday through Friday
    # Script runs on Sunday (DayOfWeek = 0). Tomorrow = Monday.
    $daysUntilMonday = ((1 - [int]$now.DayOfWeek + 7) % 7)
    if ($daysUntilMonday -eq 0) { $daysUntilMonday = 1 }
    $nextMonday = $now.AddDays($daysUntilMonday).Date
    $startDate  = $nextMonday
    $endDate    = $nextMonday.AddDays(5)   # through end of Friday
    $automationName = "Weekly Briefing"
}

Write-Log "Starting $automationName..."
Write-Log "Date range: $($startDate.ToString('yyyy-MM-dd')) to $($endDate.AddDays(-1).ToString('yyyy-MM-dd'))"

# ============================================================
# Execute
# ============================================================

try {
    # --- Authenticate ---
    Write-Log "Authenticating with Microsoft Graph..."
    $token = Get-GraphToken
    Write-Log "Authentication successful"

    # --- Fetch events ---
    Write-Log "Fetching calendar events..."
    $allEvents = Get-CalendarEvents -Token $token -StartDate $startDate -EndDate $endDate

    # --- Filter out Deep Work Block ---
    $events = $allEvents | Where-Object { $_.subject -ne "Deep Work Block" }
    $filtered = ($allEvents.Count - @($events).Count)
    Write-Log "Found $(@($events).Count) events ($filtered Deep Work Block entries filtered)"

    # ============================================================
    # Format Slack message
    # ============================================================

    if ($Mode -eq "daily") {
        $dayLabel = $startDate.ToString("dddd, MMMM d")
        $message  = "Hello Rodrigo. Here's what's on your calendar for tomorrow.`n`n*${dayLabel}:*`n"

        if (@($events).Count -eq 0) {
            $message += "No meetings scheduled. Clear day."
        }
        else {
            foreach ($ev in $events) {
                if ($ev.isAllDay) {
                    $message += "- All day: $($ev.subject)`n"
                }
                else {
                    $s = [datetime]::Parse($ev.start.dateTime).ToString("h:mm tt")
                    $e = [datetime]::Parse($ev.end.dateTime).ToString("h:mm tt")
                    $message += "- $s - ${e}: $($ev.subject)`n"
                }
            }
        }
    }
    else {
        # Weekly -- group by day, show all 5 weekdays
        $weekStart = $startDate.ToString("MMMM d")
        $weekEnd   = $endDate.AddDays(-1).ToString("MMMM d")
        $message   = "Hello Rodrigo. Here's what's on your calendar for the week ahead ($weekStart - $weekEnd).`n"

        for ($d = 0; $d -lt 5; $d++) {
            $dayDate  = $startDate.AddDays($d)
            $dayKey   = $dayDate.ToString("yyyy-MM-dd")
            $dayLabel = $dayDate.ToString("dddd, MMMM d")

            $dayEvents = @($events | Where-Object {
                [datetime]::Parse($_.start.dateTime).ToString("yyyy-MM-dd") -eq $dayKey
            })

            $message += "`n*${dayLabel}:*`n"

            if ($dayEvents.Count -eq 0) {
                $message += "  - No meetings scheduled`n"
            }
            else {
                foreach ($ev in $dayEvents) {
                    if ($ev.isAllDay) {
                        $message += "  - All day: $($ev.subject)`n"
                    }
                    else {
                        $s = [datetime]::Parse($ev.start.dateTime).ToString("h:mm tt")
                        $e = [datetime]::Parse($ev.end.dateTime).ToString("h:mm tt")
                        $message += "  - $s - ${e}: $($ev.subject)`n"
                    }
                }
            }
        }
    }

    # --- Send Slack ---
    Write-Log "Sending Slack message..."
    Send-SlackAlert -Message $message
    Write-Log "Slack message sent"

    # --- Log to Notion ---
    Log-NotionRun -AutomationName $automationName -OverallStatus "Success" -Details "Sent $(@($events).Count) events for $($startDate.ToString('yyyy-MM-dd'))"
    Write-Log "$automationName completed successfully"
}
catch {
    Write-Log "ERROR: $_"
    try {
        Send-SlackAlert -Message "$automationName failed: $_"
        Log-NotionRun -AutomationName $automationName -OverallStatus "Failed" -Details "Error: $_"
    }
    catch {
        Write-Log "Failed to send error alerts: $_"
    }
    exit 1
}
