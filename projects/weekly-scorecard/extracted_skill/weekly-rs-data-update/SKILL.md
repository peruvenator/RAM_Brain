---
name: weekly-rs-data-update
description: >
  Weekly recurring task for ReSolve Asset Management that gathers AUM/revenue data from
  an Excel file (downloaded from Dropbox), pulls sales activity metrics from HubSpot CRM,
  updates the Notion Scorecard database, and archives the source file. Trigger this skill every
  Tuesday morning or when the user asks to run the weekly RS data update, weekly scorecard
  update, weekly sales metrics pull, or update weekly RS Scorecard.
---

# Weekly RS Data Update

## Schedule

Run every **Tuesday at 6:00 AM EDT**. If triggered manually, execute immediately.

## Overview

This task gathers data from two sources (Excel file + HubSpot), updates the Notion Scorecard database, then archives the source file. Minimize browser usage - use programmatic tools (PowerShell/Python, MCP APIs) wherever possible. When browser interaction is required, always launch the default system browser (Comet) rather than a hardcoded browser.

### Execution Method Map

| Step | Method | Reason |
|---|---|---|
| Dropbox download | Default system browser (Comet) | Shared link requires it |
| Excel data extraction | PowerShell COM automation | Formulas require live Excel engine - ImportExcel and openpyxl cannot read calculated values |
| HubSpot metrics | HubSpot MCP API | Native API |
| Scorecard DB entry | Notion MCP API | Native API |
| File rename & move | Filesystem tools | Native OS operation |

## Workflow

### Phase 1 - Download Excel File (default system browser)

**Always download the file fresh - do NOT search for or check whether the file already exists before downloading.**

1. Launch the default system browser (Comet) and navigate to: `https://www.dropbox.com/scl/fi/lswac4nlysvcjx5y75270/CUs-RUs.xlsx?cloud_editor=excel&dl=1`
2. Wait for download to complete, then close the browser tab.

The file auto-downloads to: `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG`

### Phase 2 - Extract Data from Excel (programmatically)

Read `CUs-RUs.xlsx` from:
`C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG`

See [references/data-specs.md](references/data-specs.md) for the exact cell references and calculations.

**IMPORTANT:** This file contains formulas/linked data. Neither the PowerShell `ImportExcel` module nor Python `openpyxl` with `data_only=True` can read calculated values from this file - they return empty/None. Do NOT use them.

**Use PowerShell COM automation to read calculated values:**
```powershell
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Open("<full path to file>")
$ws = $wb.Sheets.Item(1)
# Read cells, e.g.: $ws.Range("AD6").Value2
$wb.Close($false)
$xl.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null
```
This opens Excel headlessly and reads live calculated values.

Store these computed values for Phase 4:
- **AUM** (in millions)
- **Units Outstanding** (whole number, last non-empty in column Q)
- **RW Units Outstanding** (whole number, last non-empty in column R)
- **Revenue Fwd 12 mth** (full dollar amount)
- **% Revenue top ETF** (decimal/percentage)
- **% Revenue top 3 ETFs** (decimal/percentage)

### Phase 3 - Gather Data from HubSpot (MCP API)

**Date range for ALL queries in this phase:**
- Start: Monday 00:00:00 of the **prior calendar week** (`GTE`) - see `references/data-specs.md` for the exact calculation
- End: Saturday 00:00:00 of that same week (`LT`)
- This captures all timestamps through end-of-day Friday regardless of time zone.

Pull the following sales activity metrics within that date range:

1. **Calls** - Number of calls made
2. **Emails** - Number of emails sent
3. **Meetings** - Number of meetings completed
4. **New Deals** - Number of new deals created
5. **Closed Deals** - Number of deals moved to "Close Won" deal stage
6. **SQLs** - Contacts whose "Lifecycle stage" updated to "Sales Qualified Lead"
7. **SALs** - Contacts whose "Lifecycle stage" updated to "Sales Accepted Lead"
8. **Deal Advancements** - Total deals entering their current pipeline stage within the date range
   - Date property: `hs_v2_date_entered_current_stage`
   - Exclude deals with `dealstage`: `closedlost` (Closed Lost) or `202649356` (Redemption)
   - Resolve stage IDs to labels using `dealstage` property options
   - Report total count only

Store all values for Phase 4.

#### Additional Phase 3 Queries (current snapshot, NOT date-filtered)

9. **Top Firm Revenue** - Query HubSpot contacts sorted by `total_revenue__assets_invested` descending, with value > 0, **excluding contact ID `36400025260` (Kent Boss)**. Retrieve the top 3 contacts.
   - **% Revenue top 1 Firm**: highest contact's `total_revenue__assets_invested` / Revenue (from Phase 2)
   - **% Revenue top 3 Firms**: sum of top 3 contacts' `total_revenue__assets_invested` / Revenue (from Phase 2)

10. **BTGD Revenue** - Fetch AUM of ETF ticker BTGD from `https://api.stockanalysis.com/api/symbol/e/BTGD/overview`, parse the `aum` field, and multiply by **0.001**.

### Phase 4 - Update Notion Scorecard (Notion MCP API)

Open via API: `https://www.notion.so/resolveam/2d93037cb38a80ffba72d26282a7a544?v=2d93037cb38a808e8c44000c3e5696bf`
- **Do NOT ask for user confirmation** - create the entry automatically. The data has been computed programmatically and does not require manual review.
- Create a **single** new entry and populate **all** of the following fields at once:
  - **Title (Week):** `Scorecard <today's date>` formatted as "Scorecard Month Day, Year" (e.g., "Scorecard February 6, 2026")
  - **Date:** Today's date (ISO format, date only, not datetime)
  - **From Phase 2:** AUM ($ Millions), Units Outstanding, RW Units Outstanding, Revenue (Fwd 12 mth), % Revenue top ETF, % Revenue top 3 ETFs
  - **From Phase 3:** Calls, Emails, Meetings, New Deals, Closed Deals, SQLs, SALs, Redemptions, Deal Advancements, % Revenue top 1 Firm, % Revenue top 3 Firms, BTGD Revenue

### Phase 5 - File Housekeeping (filesystem tools)

1. Rename `CUs-RUs.xlsx` -> `CUs-RUs YYYY-MM-DD.xlsx` (today's date) in:
   `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\Downloads RG`

2. Move the renamed file to:
   `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\Return Stacking\RS AUM Data\CU-RUs Old`
