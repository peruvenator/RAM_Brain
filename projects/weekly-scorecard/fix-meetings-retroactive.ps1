# fix-meetings-retroactive.ps1
# One-time script to correct Meetings counts in Notion scorecard DB.
# Previous runs counted ALL meetings; this re-queries HubSpot for COMPLETED only
# and patches each Notion entry from Nov 10, 2025 onward.

$ErrorActionPreference = "Stop"

# ── Load .env ────────────────────────────────────────────────────────────────
$envFile = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
        }
    }
}

$HubSpotToken = $env:HUBSPOT_TOKEN
$NotionToken  = $env:NOTION_TOKEN
$NotionDbId   = $env:NOTION_DB_ID

if (-not $HubSpotToken -or -not $NotionToken -or -not $NotionDbId) {
    throw "Missing required env vars (HUBSPOT_TOKEN, NOTION_TOKEN, NOTION_DB_ID). Check .env"
}

# ── Helper: compute prior-week range for a given Tuesday date ────────────────
function Get-PriorWeekRangeForDate {
    param([datetime]$EntryDate)
    # Entry date is a Tuesday. Prior week = Mon-to-Sat of the week before.
    $dow = [int]$EntryDate.DayOfWeek
    $daysSinceMonday = if ($dow -eq 0) { 6 } else { $dow - 1 }
    $thisMonday = $EntryDate.AddDays(-$daysSinceMonday)
    $priorMonday   = $thisMonday.AddDays(-7)
    $priorSaturday = $priorMonday.AddDays(5)

    $epoch = [datetime]"1970-01-01T00:00:00Z"
    @{
        StartMs  = [long]($priorMonday.ToUniversalTime() - $epoch).TotalMilliseconds
        EndMs    = [long]($priorSaturday.ToUniversalTime() - $epoch).TotalMilliseconds
        StartISO = $priorMonday.ToString("yyyy-MM-dd")
        EndISO   = $priorSaturday.ToString("yyyy-MM-dd")
    }
}

# ── Helper: HubSpot search (same pattern as main script) ────────────────────
function Get-CompletedMeetings {
    param([long]$StartMs, [long]$EndMs)

    $body = @{
        filterGroups = @(
            @{
                filters = @(
                    @{ propertyName = "hs_timestamp"; operator = "GTE"; value = $StartMs.ToString() }
                    @{ propertyName = "hs_timestamp"; operator = "LT";  value = $EndMs.ToString() }
                    @{ propertyName = "hs_meeting_outcome"; operator = "EQ"; value = "COMPLETED" }
                )
            }
        )
        limit = 1
    } | ConvertTo-Json -Depth 6

    $headers = @{
        Authorization  = "Bearer $HubSpotToken"
        "Content-Type" = "application/json"
    }

    $resp = Invoke-RestMethod -Uri "https://api.hubapi.com/crm/v3/objects/meetings/search" `
        -Method POST -Headers $headers -Body $body
    return $resp.total
}

# ── Step 1: Query Notion for all entries from Nov 10, 2025 onward ────────────
Write-Host "`n=== Querying Notion scorecard DB for entries >= 2025-11-10 ===`n"

$notionHeaders = @{
    Authorization    = "Bearer $NotionToken"
    "Content-Type"   = "application/json"
    "Notion-Version" = "2022-06-28"
}

$allPages = @()
$hasMore  = $true
$cursor   = $null

while ($hasMore) {
    $queryBody = @{
        filter = @{
            property = "Date"
            date     = @{ on_or_after = "2025-11-10" }
        }
        sorts = @(
            @{ property = "Date"; direction = "ascending" }
        )
        page_size = 100
    }
    if ($cursor) { $queryBody.start_cursor = $cursor }

    $queryJson = $queryBody | ConvertTo-Json -Depth 6
    $resp = Invoke-RestMethod -Uri "https://api.notion.com/v1/databases/$NotionDbId/query" `
        -Method POST -Headers $notionHeaders -Body $queryJson

    $allPages += $resp.results
    $hasMore = $resp.has_more
    $cursor  = $resp.next_cursor
}

Write-Host "Found $($allPages.Count) entries to correct.`n"

if ($allPages.Count -eq 0) {
    Write-Host "No entries found. Exiting."
    exit 0
}

# ── Step 2: For each entry, re-query HubSpot and patch Notion ────────────────
$results = @()

foreach ($page in $allPages) {
    $pageId    = $page.id
    $dateValue = $page.properties.Date.date.start
    $title     = ($page.properties.Week.title | ForEach-Object { $_.plain_text }) -join ""
    $oldCount  = $page.properties.Meetings.number

    $entryDate = [datetime]::Parse($dateValue)
    $range     = Get-PriorWeekRangeForDate -EntryDate $entryDate

    $newCount  = Get-CompletedMeetings -StartMs $range.StartMs -EndMs $range.EndMs

    $changed = $oldCount -ne $newCount
    $marker  = if ($changed) { " <-- CHANGED" } else { "" }

    Write-Host "$title | Date=$dateValue | Week=$($range.StartISO)..$($range.EndISO) | Old=$oldCount | New=$newCount$marker"

    $results += [PSCustomObject]@{
        Title    = $title
        Date     = $dateValue
        WeekRange = "$($range.StartISO)..$($range.EndISO)"
        Old      = $oldCount
        New      = $newCount
        Changed  = $changed
        PageId   = $pageId
    }

    # Patch Notion if the value changed
    if ($changed) {
        $patchBody = @{
            properties = @{
                Meetings = @{ number = [int]$newCount }
            }
        } | ConvertTo-Json -Depth 6

        Invoke-RestMethod -Uri "https://api.notion.com/v1/pages/$pageId" `
            -Method PATCH -Headers $notionHeaders -Body $patchBody | Out-Null
    }

    # Small delay to respect rate limits
    Start-Sleep -Milliseconds 200
}

# ── Summary ──────────────────────────────────────────────────────────────────
$changedCount = ($results | Where-Object { $_.Changed }).Count
Write-Host "`n=== Summary ==="
Write-Host "Total entries checked: $($results.Count)"
Write-Host "Entries corrected:     $changedCount"
Write-Host "Entries unchanged:     $($results.Count - $changedCount)"

if ($changedCount -gt 0) {
    Write-Host "`nCorrected entries:"
    $results | Where-Object { $_.Changed } | ForEach-Object {
        Write-Host "  $($_.Title): $($_.Old) -> $($_.New)"
    }
}

Write-Host "`nDone."
