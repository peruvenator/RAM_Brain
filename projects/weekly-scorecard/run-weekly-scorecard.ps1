# run-weekly-scorecard.ps1
# Self-contained weekly scorecard automation -- no LLM/MCP dependencies.
# Phases: 1) Dropbox download  2) Excel extraction  3) HubSpot API  4) Notion API  5) File archive

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

# ── Validate required secrets ────────────────────────────────────────────────
$requiredVars = @("HUBSPOT_TOKEN","NOTION_TOKEN","NOTION_DB_ID","NOTION_RUNS_DB_ID","NOTION_INVENTORY_DB_ID","SLACK_WEBHOOK")
$missing = $requiredVars | Where-Object { -not [Environment]::GetEnvironmentVariable($_, "Process") }
if ($missing) {
    throw "Missing required environment variables: $($missing -join ', '). Ensure rs_weekly_scorecard/.env exists and contains all keys."
}

# ── Configuration ────────────────────────────────────────────────────────────
$Config = @{
    # Dropbox
    DropboxUrl   = "https://www.dropbox.com/scl/fi/lswac4nlysvcjx5y75270/CUs-RUs.xlsx?cloud_editor=excel&dl=1"
    DownloadDir  = "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG"
    FileName     = "CUs-RUs.xlsx"

    # Archive
    ArchiveDir   = "C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\Return Stacking\RS AUM Data\CU-RUs Old"

    # HubSpot
    HubSpotToken = $env:HUBSPOT_TOKEN
    HubSpotBase  = "https://api.hubapi.com/crm/v3/objects"

    # Notion
    NotionToken  = $env:NOTION_TOKEN
    NotionDbId   = $env:NOTION_DB_ID

    # Slack
    SlackWebhook = $env:SLACK_WEBHOOK

    # Notion Automation Runs DB (for run tracking)
    NotionRunsDbId      = $env:NOTION_RUNS_DB_ID
    NotionInventoryDbId = $env:NOTION_INVENTORY_DB_ID

    # Logging
    ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
}

$Config.LogDir  = Join-Path $Config.ScriptDir "logs"
$Config.ExcelPath = Join-Path $Config.DownloadDir $Config.FileName

# ── Logging ──────────────────────────────────────────────────────────────────
if (-not (Test-Path $Config.LogDir)) {
    New-Item -ItemType Directory -Path $Config.LogDir | Out-Null
}
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile   = Join-Path $Config.LogDir "scorecard_$timestamp.log"

function Write-Log {
    param([string]$Message)
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $entry
    $entry | Out-File -FilePath $logFile -Append -Encoding utf8
}

# ── Shared helpers (Slack alerts, Notion run logging) ────────────────────────
. (Join-Path $Config.ScriptDir "automation-helpers.ps1")

# ── Phase tracking ───────────────────────────────────────────────────────────
$PhaseStatus = @{
    Phase1 = "skipped"
    Phase2 = "skipped"
    Phase3 = "skipped"
    Phase4 = "skipped"
    Phase5 = "skipped"
}
$ExcelData   = @{}
$HubSpotData = @{}

# ── Phase 1: Dropbox Download ───────────────────────────────────────────────
function Invoke-Phase1 {
    Write-Log "=== Phase 1: Dropbox Download ==="

    # Delete stale file if present
    if (Test-Path $Config.ExcelPath) {
        Remove-Item $Config.ExcelPath -Force
        Write-Log "Deleted stale $($Config.FileName)"
    }

    # Open Dropbox URL in default browser
    Start-Process $Config.DropboxUrl
    Write-Log "Opened Dropbox URL in default browser"

    # Poll for file existence
    $maxWait = 120
    $elapsed = 0
    $interval = 5
    while (-not (Test-Path $Config.ExcelPath) -and $elapsed -lt $maxWait) {
        Start-Sleep -Seconds $interval
        $elapsed += $interval
        Write-Log "Waiting for download... ${elapsed}s"
    }

    if (-not (Test-Path $Config.ExcelPath)) {
        throw "Download timed out after ${maxWait}s -- file not found"
    }

    # Wait for file size to stabilize (not still downloading)
    $prevSize = -1
    for ($i = 0; $i -lt 6; $i++) {
        $curSize = (Get-Item $Config.ExcelPath).Length
        if ($curSize -eq $prevSize -and $curSize -gt 0) {
            Write-Log "Download complete: $curSize bytes"
            return
        }
        $prevSize = $curSize
        Start-Sleep -Seconds 2
    }

    # If we got here, file exists but size may still be changing -- proceed anyway
    Write-Log "File present ($prevSize bytes), proceeding"
}

# ── Phase 2: Excel COM Automation ────────────────────────────────────────────
function Invoke-Phase2 {
    Write-Log "=== Phase 2: Excel Data Extraction ==="
    $xl = $null
    try {
        Write-Log "Creating Excel COM object..."
        $xl = New-Object -ComObject Excel.Application
        $xl.Visible = $false
        $xl.DisplayAlerts = $false
        Write-Log "Excel COM created, opening file: $($Config.ExcelPath)"

        # Verify file exists and is readable
        $fileInfo = Get-Item $Config.ExcelPath
        Write-Log "File size: $($fileInfo.Length) bytes, last write: $($fileInfo.LastWriteTime)"

        $wb = $xl.Workbooks.Open($Config.ExcelPath)
        if ($null -eq $wb) { throw "Workbooks.Open returned null" }
        Write-Log "Workbook opened, sheets count: $($wb.Sheets.Count)"

        $ws = $wb.Sheets.Item(1)
        if ($null -eq $ws) { throw "Sheets.Item(1) returned null" }
        Write-Log "Opened workbook, sheet: $($ws.Name)"

        # Wait for Excel to finish calculating (xlDone = 0)
        Start-Sleep -Seconds 5
        $calcWait = 0
        while ($xl.CalculationState -ne 0 -and $calcWait -lt 30) {
            Start-Sleep -Seconds 1
            $calcWait++
        }
        Write-Log "Excel calculations complete (waited ${calcWait}s extra)"

        # AUM from AD6 (divide by 1M)
        $aumRaw = $ws.Range("AD6").Value2
        $ExcelData['AUM'] = [math]::Round($aumRaw / 1000000, 2)
        Write-Log "AUM raw=$aumRaw  millions=$($ExcelData['AUM'])"

        # Revenue (Fwd 12 mth) from AE19
        $ExcelData['Revenue'] = $ws.Range("AE19").Value2
        Write-Log "Revenue=$($ExcelData['Revenue'])"

        # Units Outstanding -- last non-empty value in column Q
        $lastRow = $ws.Cells($ws.Rows.Count, "Q").End(-4162).Row   # xlUp = -4162
        $ExcelData['Units'] = $ws.Range("Q$lastRow").Value2
        Write-Log "Units=$($ExcelData['Units']) (row $lastRow)"

        # RW Units Outstanding -- last non-empty value in column R
        $lastRowR = $ws.Cells($ws.Rows.Count, "R").End(-4162).Row   # xlUp = -4162
        $ExcelData['RWUnits'] = [math]::Round($ws.Range("R$lastRowR").Value2, 0)
        Write-Log "RW Units=$($ExcelData['RWUnits']) (row $lastRowR)"

        # Individual ETF revenue -- U14:AA14
        $etfColMap = [ordered]@{
            "U"  = "RSBT_Revenue"
            "V"  = "RSST_Revenue"
            "W"  = "RSSB_Revenue"
            "X"  = "RSSY_Revenue"
            "Y"  = "RSBY_Revenue"
            "Z"  = "RSBA_Revenue"
            "AA" = "RSSX_Revenue"
        }
        $revenueValues = @()
        foreach ($col in $etfColMap.Keys) {
            $val = $ws.Range("${col}14").Value2
            if ($null -ne $val -and $val -ne "") {
                $ExcelData[$etfColMap[$col]] = [double]$val
                $revenueValues += [double]$val
                Write-Log "  $($etfColMap[$col])=$val"
            }
        }

        # Revenue concentration from individual ETF values
        $sorted = $revenueValues | Sort-Object -Descending
        $ExcelData['PctTopETF']  = [math]::Round($sorted[0] / $ExcelData['Revenue'], 3)
        $ExcelData['PctTop3ETF'] = [math]::Round((($sorted[0..2] | Measure-Object -Sum).Sum) / $ExcelData['Revenue'], 3)
        Write-Log "% Top ETF=$($ExcelData['PctTopETF'])  % Top 3=$($ExcelData['PctTop3ETF'])"

        $wb.Close($false)
        Write-Log "Workbook closed"
    }
    finally {
        if ($null -ne $xl) {
            $xl.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
            [GC]::Collect()
            [GC]::WaitForPendingFinalizers()
            Write-Log "Excel COM released"
        }
    }
}

# ── Phase 3: HubSpot REST API ───────────────────────────────────────────────
function Get-PriorWeekRange {
    # Returns @{ StartMs = ...; EndMs = ... } for prior calendar week Mon 00:00 UTC to Sat 00:00 UTC
    $today = (Get-Date).Date
    # DayOfWeek: Sunday=0, Monday=1 ... Saturday=6
    $dow = [int]$today.DayOfWeek
    # Days since this week's Monday (Sunday wraps to 7)
    $daysSinceMonday = if ($dow -eq 0) { 6 } else { $dow - 1 }
    # This week's Monday
    $thisMonday = $today.AddDays(-$daysSinceMonday)
    # Prior week's Monday
    $priorMonday = $thisMonday.AddDays(-7)
    $priorSaturday = $priorMonday.AddDays(5)

    $epoch = [datetime]"1970-01-01T00:00:00Z"
    @{
        StartMs  = [long]($priorMonday.ToUniversalTime() - $epoch).TotalMilliseconds
        EndMs    = [long]($priorSaturday.ToUniversalTime() - $epoch).TotalMilliseconds
        StartISO = $priorMonday.ToString("yyyy-MM-dd")
        EndISO   = $priorSaturday.ToString("yyyy-MM-dd")
    }
}

function Invoke-HubSpotSearch {
    param(
        [string]$ObjectType,
        [string]$DateProperty,
        [long]$StartMs,
        [long]$EndMs,
        [hashtable[]]$ExtraFilters = @()
    )

    $filters = @(
        @{ propertyName = $DateProperty; operator = "GTE"; value = $StartMs.ToString() }
        @{ propertyName = $DateProperty; operator = "LT";  value = $EndMs.ToString() }
    ) + $ExtraFilters

    $body = @{
        filterGroups = @( @{ filters = $filters } )
        limit        = 1
    } | ConvertTo-Json -Depth 6

    $headers = @{
        Authorization  = "Bearer $($Config.HubSpotToken)"
        "Content-Type" = "application/json"
    }

    $url = "$($Config.HubSpotBase)/$ObjectType/search"

    try {
        $resp = Invoke-RestMethod -Uri $url -Method POST -Headers $headers -Body $body
        return $resp.total
    }
    catch {
        $status = $null
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        Write-Log "  HTTP $status error for $ObjectType/$DateProperty -- returning N/A"
        return "N/A"
    }
}

function Invoke-Phase3 {
    Write-Log "=== Phase 3: HubSpot Metrics ==="

    $range = Get-PriorWeekRange
    Write-Log "Date range: $($range.StartISO) to $($range.EndISO) (ms: $($range.StartMs) - $($range.EndMs))"

    # 1. Calls
    $HubSpotData['Calls'] = Invoke-HubSpotSearch -ObjectType "calls" -DateProperty "hs_timestamp" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "Calls=$($HubSpotData['Calls'])"

    # 2. Emails
    $HubSpotData['Emails'] = Invoke-HubSpotSearch -ObjectType "emails" -DateProperty "hs_timestamp" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "Emails=$($HubSpotData['Emails'])"

    # 3. Meetings
    $HubSpotData['Meetings'] = Invoke-HubSpotSearch -ObjectType "meetings" -DateProperty "hs_timestamp" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "Meetings=$($HubSpotData['Meetings'])"

    # 4. New Deals
    $HubSpotData['NewDeals'] = Invoke-HubSpotSearch -ObjectType "deals" -DateProperty "createdate" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "New Deals=$($HubSpotData['NewDeals'])"

    # 5. Closed Deals (entered Closed Won stage)
    $HubSpotData['ClosedDeals'] = Invoke-HubSpotSearch -ObjectType "deals" `
        -DateProperty "hs_v2_date_entered_closedwon" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "Closed Deals=$($HubSpotData['ClosedDeals'])"

    # 6. SQLs (lifecycle stage = opportunity)
    $HubSpotData['SQLs'] = Invoke-HubSpotSearch -ObjectType "contacts" `
        -DateProperty "hs_v2_date_entered_opportunity" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "SQLs=$($HubSpotData['SQLs'])"

    # 7. SALs (lifecycle stage = 198524938)
    $HubSpotData['SALs'] = Invoke-HubSpotSearch -ObjectType "contacts" `
        -DateProperty "hs_v2_date_entered_198524938" `
        -StartMs $range.StartMs -EndMs $range.EndMs
    Write-Log "SALs=$($HubSpotData['SALs'])"

    # 8. Deal Advancements (exclude closedlost and 202649356/Redemption)
    $HubSpotData['DealAdvancements'] = Invoke-HubSpotSearch -ObjectType "deals" `
        -DateProperty "hs_v2_date_entered_current_stage" `
        -StartMs $range.StartMs -EndMs $range.EndMs `
        -ExtraFilters @(
            @{ propertyName = "dealstage"; operator = "NOT_IN"; values = @("closedlost", "202649356") }
        )
    Write-Log "Deal Advancements=$($HubSpotData['DealAdvancements'])"

    # 9. Redemptions (stage = 202649356)
    $HubSpotData['Redemptions'] = Invoke-HubSpotSearch -ObjectType "deals" `
        -DateProperty "hs_v2_date_entered_current_stage" `
        -StartMs $range.StartMs -EndMs $range.EndMs `
        -ExtraFilters @(
            @{ propertyName = "dealstage"; operator = "EQ"; value = "202649356" }
        )
    Write-Log "Redemptions=$($HubSpotData['Redemptions'])"

    # 10. Top Firm Revenue (current snapshot, not date-filtered)
    Get-TopFirmRevenue

    # 11. BTGD Revenue (AUM from web API × 0.001)
    Get-BTGDRevenue
}

function Get-TopFirmRevenue {
    Write-Log "--- Top Firm Revenue (HubSpot) ---"

    $headers = @{
        Authorization  = "Bearer $($Config.HubSpotToken)"
        "Content-Type" = "application/json"
    }

    # Exclude Kent Boss (contact ID 36400025260) and filter for non-zero revenue
    $body = @{
        filterGroups = @(
            @{
                filters = @(
                    @{ propertyName = "total_revenue__assets_invested"; operator = "GT"; value = "0" }
                    @{ propertyName = "hs_object_id"; operator = "NEQ"; value = "36400025260" }
                )
            }
        )
        sorts = @(
            @{ propertyName = "total_revenue__assets_invested"; direction = "DESCENDING" }
        )
        properties = @("total_revenue__assets_invested", "firstname", "lastname")
        limit = 3
    } | ConvertTo-Json -Depth 6

    $url = "$($Config.HubSpotBase)/contacts/search"

    try {
        $resp = Invoke-RestMethod -Uri $url -Method POST -Headers $headers -Body $body

        if ($resp.results.Count -lt 3) {
            Write-Log "WARNING: Only $($resp.results.Count) contacts found with revenue > 0"
        }

        $values = @()
        foreach ($contact in $resp.results) {
            $rev = [double]$contact.properties.total_revenue__assets_invested
            $name = "$($contact.properties.firstname) $($contact.properties.lastname)"
            $values += $rev
            Write-Log "  Firm: $name = $rev"
        }

        $HubSpotData['TopFirmRevenues'] = $values
        Write-Log "Top firm revenues collected: $($values.Count) contacts"
    }
    catch {
        Write-Log "Top Firm Revenue query FAILED: $_"
        $HubSpotData['TopFirmRevenues'] = $null
    }
}

function Get-BTGDRevenue {
    Write-Log "--- BTGD Revenue (Web API) ---"

    try {
        $resp = Invoke-RestMethod -Uri "https://api.stockanalysis.com/api/symbol/e/BTGD/overview" -Method GET
        $aumStr = $resp.data.aum   # e.g. "$77.67M"

        # Parse: strip "$", handle "M" (millions) or "B" (billions)
        $cleaned = $aumStr -replace '[\$,]', ''
        $multiplier = 1
        if ($cleaned -match '([0-9.]+)([MB])') {
            $numVal = [double]$Matches[1]
            if ($Matches[2] -eq 'M') { $multiplier = 1000000 }
            elseif ($Matches[2] -eq 'B') { $multiplier = 1000000000 }
            $aumRaw = $numVal * $multiplier
        } else {
            $aumRaw = [double]$cleaned
        }

        $btgdRevenue = [math]::Round($aumRaw * 0.001)
        $HubSpotData['BTGDRevenue'] = $btgdRevenue
        Write-Log "BTGD AUM=$aumStr  AUM_raw=$aumRaw  Revenue (x0.001)=$btgdRevenue"
    }
    catch {
        Write-Log "BTGD Revenue fetch FAILED: $_"
        $HubSpotData['BTGDRevenue'] = $null
    }
}

# ── Phase 4: Notion API ─────────────────────────────────────────────────────
function Invoke-Phase4 {
    Write-Log "=== Phase 4: Notion Scorecard Entry ==="

    $todayDate = (Get-Date).ToString("yyyy-MM-dd")
    $titleText = "Scorecard " + (Get-Date).ToString("MMMM d, yyyy")

    $headers = @{
        Authorization    = "Bearer $($Config.NotionToken)"
        "Content-Type"   = "application/json"
        "Notion-Version" = "2022-06-28"
    }

    # ── Step A: Query for existing entry with today's date ──
    $queryBody = @{
        filter = @{
            property = "Date"
            date     = @{ equals = $todayDate }
        }
    } | ConvertTo-Json -Depth 6

    $queryResp = Invoke-RestMethod -Uri "https://api.notion.com/v1/databases/$($Config.NotionDbId)/query" `
        -Method POST -Headers $headers -Body $queryBody

    $existingPage = $null
    $existingProps = @{}
    if ($queryResp.results.Count -gt 0) {
        $existingPage = $queryResp.results[0]
        $existingProps = $existingPage.properties
        Write-Log "Found existing entry: id=$($existingPage.id)"
    }
    else {
        Write-Log "No existing entry for $todayDate -- will create new"
    }

    # ── Step B: Build properties to write ──
    $properties = @{
        "Week" = @{
            title = @( @{ text = @{ content = $titleText } } )
        }
        "Date" = @{
            date = @{ start = $todayDate }
        }
    }

    # Excel fields
    if ($ExcelData.Count -gt 0) {
        if ($null -ne $ExcelData['AUM'])       { $properties['AUM ($ Millions)']    = @{ number = $ExcelData['AUM'] } }
        if ($null -ne $ExcelData['Units'])      { $properties['Units Outstanding']    = @{ number = $ExcelData['Units'] } }
        if ($null -ne $ExcelData['Revenue'])    { $properties['Revenue (Fwd 12 mth)'] = @{ number = $ExcelData['Revenue'] } }
        if ($null -ne $ExcelData['PctTopETF'])  { $properties['% Revenue top ETF']    = @{ number = $ExcelData['PctTopETF'] } }
        if ($null -ne $ExcelData['PctTop3ETF']) { $properties['% Revenue top 3 ETFs'] = @{ number = $ExcelData['PctTop3ETF'] } }
    }

    # RW Units Outstanding
    if ($ExcelData.Count -gt 0) {
        if ($null -ne $ExcelData['RWUnits'])   { $properties['RW Units Outstanding'] = @{ number = $ExcelData['RWUnits'] } }
    }

    # Individual ETF revenue fields
    if ($ExcelData.Count -gt 0) {
        if ($null -ne $ExcelData['RSBT_Revenue']) { $properties['RSBT Revenue'] = @{ number = $ExcelData['RSBT_Revenue'] } }
        if ($null -ne $ExcelData['RSST_Revenue']) { $properties['RSST Revenue'] = @{ number = $ExcelData['RSST_Revenue'] } }
        if ($null -ne $ExcelData['RSSB_Revenue']) { $properties['RSSB Revenue'] = @{ number = $ExcelData['RSSB_Revenue'] } }
        if ($null -ne $ExcelData['RSSY_Revenue']) { $properties['RSSY Revenue'] = @{ number = $ExcelData['RSSY_Revenue'] } }
        if ($null -ne $ExcelData['RSBY_Revenue']) { $properties['RSBY Revenue'] = @{ number = $ExcelData['RSBY_Revenue'] } }
        if ($null -ne $ExcelData['RSBA_Revenue']) { $properties['RSBA Revenue'] = @{ number = $ExcelData['RSBA_Revenue'] } }
        if ($null -ne $ExcelData['RSSX_Revenue']) { $properties['RSSX Revenue'] = @{ number = $ExcelData['RSSX_Revenue'] } }
    }

    # HubSpot fields
    $hsFieldMap = @{
        'Calls'            = ' Calls'
        'Emails'           = 'Emails'
        'Meetings'         = 'Meetings'
        'NewDeals'         = 'New Deals'
        'ClosedDeals'      = 'Closed Deals'
        'SQLs'             = 'SQLs'
        'SALs'             = 'SALs'
        'Redemptions'      = 'Redemptions'
        'DealAdvancements' = 'Deal Advancements'
    }
    foreach ($key in $hsFieldMap.Keys) {
        $val = $HubSpotData[$key]
        if ($null -ne $val -and $val -ne "N/A") {
            $properties[$hsFieldMap[$key]] = @{ number = [int]$val }
        }
    }

    # Firm revenue concentration (from HubSpot top contacts / Excel revenue)
    if ($null -ne $HubSpotData['TopFirmRevenues'] -and $HubSpotData['TopFirmRevenues'].Count -ge 1 -and $null -ne $ExcelData['Revenue'] -and $ExcelData['Revenue'] -gt 0) {
        $firmRevs = $HubSpotData['TopFirmRevenues']

        # % Revenue top 1 Firm
        $pctTop1Firm = [math]::Round($firmRevs[0] / $ExcelData['Revenue'], 3)
        $properties['% Revenue top 1 Firm'] = @{ number = $pctTop1Firm }
        Write-Log "% Revenue top 1 Firm = $pctTop1Firm"

        # % Revenue top 3 Firms
        if ($firmRevs.Count -ge 3) {
            $top3Sum = ($firmRevs[0..2] | Measure-Object -Sum).Sum
            $pctTop3Firms = [math]::Round($top3Sum / $ExcelData['Revenue'], 3)
            $properties['% Revenue top 3 Firms'] = @{ number = $pctTop3Firms }
            Write-Log "% Revenue top 3 Firms = $pctTop3Firms"
        }
    }

    # BTGD Revenue
    if ($null -ne $HubSpotData['BTGDRevenue']) {
        $properties['BTGD Revenue'] = @{ number = $HubSpotData['BTGDRevenue'] }
    }

    # ── If existing page found, skip already-populated fields ──
    if ($null -ne $existingPage) {
        $keysToRemove = @()
        foreach ($propName in $properties.Keys) {
            # Always keep identity fields
            if ($propName -eq "Week" -or $propName -eq "Date") { continue }

            $existing = $existingProps.$propName
            if ($null -ne $existing) {
                # Check if the existing field has a value (number property)
                if ($null -ne $existing.number) {
                    Write-Log "  Skipping '$propName' -- already populated ($($existing.number))"
                    $keysToRemove += $propName
                }
            }
        }
        foreach ($k in $keysToRemove) {
            $properties.Remove($k)
        }
    }

    # ── Step C: Write to Notion ──
    if ($null -ne $existingPage) {
        # PATCH existing page with only empty fields
        $body = @{
            properties = $properties
        } | ConvertTo-Json -Depth 10

        $resp = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages/$($existingPage.id)" `
            -Method PATCH -Headers $headers -Body $body
        Write-Log "Notion entry updated: $titleText (id=$($resp.id), fields written=$($properties.Count - 2))"
    }
    else {
        # POST new page
        $body = @{
            parent     = @{ database_id = $Config.NotionDbId }
            properties = $properties
        } | ConvertTo-Json -Depth 10

        $resp = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" -Method POST -Headers $headers -Body $body
        Write-Log "Notion entry created: $titleText (id=$($resp.id))"
    }
}

# ── Phase 5: File Archive ───────────────────────────────────────────────────
function Invoke-Phase5 {
    Write-Log "=== Phase 5: File Archive ==="

    $dateSuffix = (Get-Date).ToString("yyyy-MM-dd")
    $newName    = "CUs-RUs $dateSuffix.xlsx"
    $newPath    = Join-Path $Config.DownloadDir $newName

    # Rename
    Rename-Item -Path $Config.ExcelPath -NewName $newName
    Write-Log "Renamed to $newName"

    # Ensure archive dir exists
    if (-not (Test-Path $Config.ArchiveDir)) {
        New-Item -ItemType Directory -Path $Config.ArchiveDir -Force | Out-Null
        Write-Log "Created archive directory"
    }

    # Move
    $destPath = Join-Path $Config.ArchiveDir $newName
    Move-Item -Path $newPath -Destination $destPath -Force
    Write-Log "Moved to $destPath"
}

# ── Orchestrator ─────────────────────────────────────────────────────────────
Write-Log "===== Weekly Scorecard Run Started ====="
Write-Log "Script dir: $($Config.ScriptDir)"

# Phase 1
try {
    Invoke-Phase1
    $PhaseStatus.Phase1 = "success"
}
catch {
    $PhaseStatus.Phase1 = "FAILED: $_"
    Write-Log "Phase 1 FAILED: $_"
}

# Phase 2 (depends on Phase 1)
if ($PhaseStatus.Phase1 -eq "success") {
    try {
        Invoke-Phase2
        $PhaseStatus.Phase2 = "success"
    }
    catch {
        $PhaseStatus.Phase2 = "FAILED: $_"
        Write-Log "Phase 2 FAILED: $_"
    }
}
else {
    Write-Log "Phase 2 skipped -- no file from Phase 1"
}

# Phase 3 (independent)
try {
    Invoke-Phase3
    $PhaseStatus.Phase3 = "success"
}
catch {
    $PhaseStatus.Phase3 = "FAILED: $_"
    Write-Log "Phase 3 FAILED: $_"
}

# Phase 4 (runs with whatever data is available)
try {
    Invoke-Phase4
    $PhaseStatus.Phase4 = "success"
}
catch {
    $PhaseStatus.Phase4 = "FAILED: $_"
    Write-Log "Phase 4 FAILED: $_"
}

# Phase 5 (depends on Phase 1)
if ($PhaseStatus.Phase1 -eq "success") {
    try {
        Invoke-Phase5
        $PhaseStatus.Phase5 = "success"
    }
    catch {
        $PhaseStatus.Phase5 = "FAILED: $_"
        Write-Log "Phase 5 FAILED: $_"
    }
}
else {
    Write-Log "Phase 5 skipped -- no file from Phase 1"
}

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Log ""
Write-Log "===== Run Summary ====="
Write-Log "Phase 1 (Dropbox Download): $($PhaseStatus.Phase1)"
Write-Log "Phase 2 (Excel Extraction): $($PhaseStatus.Phase2)"
Write-Log "Phase 3 (HubSpot Metrics):  $($PhaseStatus.Phase3)"
Write-Log "Phase 4 (Notion Entry):     $($PhaseStatus.Phase4)"
Write-Log "Phase 5 (File Archive):     $($PhaseStatus.Phase5)"
Write-Log ""

if ($ExcelData.Count -gt 0) {
    Write-Log "Excel Data:"
    Write-Log "  AUM (millions):    $($ExcelData['AUM'])"
    Write-Log "  Revenue:           $($ExcelData['Revenue'])"
    Write-Log "  Units Outstanding: $($ExcelData['Units'])"
    Write-Log "  RW Units:          $($ExcelData['RWUnits'])"
    Write-Log "  % Top ETF:         $($ExcelData['PctTopETF'])"
    Write-Log "  % Top 3 ETFs:      $($ExcelData['PctTop3ETF'])"
    Write-Log "  ETF Revenue:"
    Write-Log "    RSBT: $($ExcelData['RSBT_Revenue'])"
    Write-Log "    RSST: $($ExcelData['RSST_Revenue'])"
    Write-Log "    RSSB: $($ExcelData['RSSB_Revenue'])"
    Write-Log "    RSSY: $($ExcelData['RSSY_Revenue'])"
    Write-Log "    RSBY: $($ExcelData['RSBY_Revenue'])"
    Write-Log "    RSBA: $($ExcelData['RSBA_Revenue'])"
    Write-Log "    RSSX: $($ExcelData['RSSX_Revenue'])"
}

if ($HubSpotData.Count -gt 0) {
    Write-Log "HubSpot Data:"
    foreach ($key in $HubSpotData.Keys) {
        if ($key -eq 'TopFirmRevenues') {
            Write-Log "  TopFirmRevenues: $($HubSpotData[$key] -join ', ')"
        } else {
            Write-Log "  ${key}: $($HubSpotData[$key])"
        }
    }
}

# ── Slack + Notion run logging ───────────────────────────────────────────────
$failedPhases = @()
foreach ($key in @("Phase1","Phase2","Phase3","Phase4","Phase5")) {
    if ($PhaseStatus[$key] -match "^FAILED") {
        $failedPhases += "$key : $($PhaseStatus[$key])"
    }
}

$overallStatus = if ($failedPhases.Count -gt 0) { "Failed" } else { "Success" }

# Build details summary
$detailLines = @(
    "Phase 1 (Dropbox): $($PhaseStatus.Phase1)"
    "Phase 2 (Excel):   $($PhaseStatus.Phase2)"
    "Phase 3 (HubSpot): $($PhaseStatus.Phase3)"
    "Phase 4 (Notion):  $($PhaseStatus.Phase4)"
    "Phase 5 (Archive): $($PhaseStatus.Phase5)"
)
if ($ExcelData.Count -gt 0) {
    $detailLines += "AUM=$($ExcelData['AUM'])M  Rev=$($ExcelData['Revenue'])  Units=$($ExcelData['Units'])"
}
$detailText = $detailLines -join "`n"

# Log to Notion Automation Runs DB (always)
Log-NotionRun -AutomationName "Weekly Scorecard" -OverallStatus $overallStatus -Details $detailText

# Send Slack alert (only on failure)
if ($failedPhases.Count -gt 0) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm"
    $failList = $failedPhases -join "`n"
    $logName = Split-Path $logFile -Leaf
    $slackMsg = ":warning: *Weekly Scorecard* failed at $ts`n$failList`nLog: $logName"
    Send-SlackAlert -Message $slackMsg
}

Write-Log ""
Write-Log "===== Run Complete ====="

# ── Log cleanup: delete logs older than 90 days ─────────────────────────────
Get-ChildItem -Path $Config.LogDir -Filter "scorecard_*.log" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } |
    Remove-Item -Force
