# Automations Registry

Central inventory of all automated scripts. Future Claude sessions should read this file first.

## Shared Module

`C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\automation-helpers.ps1`

Every automation dot-sources this file to get `Send-SlackAlert`, `Log-NotionRun`, and `Update-InventoryStatus`. The calling script must define `$Config` with keys: `NotionToken`, `SlackWebhook`, `NotionRunsDbId`, `NotionInventoryDbId`. It must also define `$logFile` and a `Write-Log` function.

## Weekly Scorecard

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\run-weekly-scorecard.ps1` |
| Wrapper | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\run-weekly-scorecard.bat` |
| Schedule | Every Tuesday 5 AM (Windows Task Scheduler) |
| Shortcut | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\weekly-scorecard\shortcuts\Run Weekly Scorecard.bat` |
| Description | Downloads CUs-RUs.xlsx from Dropbox, extracts AUM/Revenue/Units via Excel COM, pulls HubSpot CRM metrics (calls, emails, meetings, deals, SQLs, SALs), writes weekly entry to Notion "Weekly AUM Growth" DB, archives file. |

### Notion Databases

| Database | ID | Purpose |
|---|---|---|
| Weekly AUM Growth | `2d93037cb38a80ffba72d26282a7a544` | Weekly scorecard data entries |
| Automation Runs | `3023037cb38a815fb09fd3d2b6f71ae7` | Run history log (success/failure per run) |
| Automations Inventory | `3023037cb38a814bac81cb56a89af346` | Central inventory of all automations |

### Alerting

- **Slack**: Webhook posts to channel on failure only
- **Notion**: Every run (success or failure) logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run

---

## Daily Calendar Briefing

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\daily-briefing\run-briefing.ps1 -Mode daily` |
| Wrapper | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\daily-briefing\run-daily-briefing.bat` |
| Schedule | Every day at 8:00 PM ET (Windows Task Scheduler) |
| Description | Fetches tomorrow's calendar events via Microsoft Graph API, filters out "Deep Work Block" entries, sends formatted schedule to Slack. |

### Alerting

- **Slack**: Sends the briefing message (or error alert on failure)
- **Notion**: Every run logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run

---

## Weekly Calendar Briefing

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\daily-briefing\run-briefing.ps1 -Mode weekly` |
| Wrapper | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\daily-briefing\run-weekly-briefing.bat` |
| Schedule | Every Sunday at 8:00 PM ET (Windows Task Scheduler) |
| Description | Fetches Mon-Fri calendar events for the coming week via Microsoft Graph API, filters out "Deep Work Block" entries, groups by day, sends formatted week-ahead summary to Slack. |

### Notion Databases

Shares the same logging databases as all other automations:

| Database | ID | Purpose |
|---|---|---|
| Automation Runs | `3023037cb38a815fb09fd3d2b6f71ae7` | Run history log (success/failure per run) |
| Automations Inventory | `3023037cb38a814bac81cb56a89af346` | Central inventory of all automations |

### Alerting

- **Slack**: Sends the briefing message (or error alert on failure)
- **Notion**: Every run logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run

---

## AT Widget Rebuild

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\all-terrain-weights-widget\rebuild-widget.ps1` |
| Wrapper | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\all-terrain-weights-widget\rebuild-widget.bat` |
| Schedule | Every day at 5:00 AM ET (Windows Task Scheduler) |
| Task name | `AT Widget Rebuild` |
| Description | Checks if source CSVs (weights_beta.csv, weights_alpha.csv) have been modified since the last HTML build. If so, runs `python build_widget.py` to regenerate the self-contained HTML widget. Skips rebuild if data is unchanged. |

### Change Detection

Compares `LastWriteTime` of source CSVs against the output HTML. Rebuild only triggers when source data is newer.

### Alerting

- **Slack**: Webhook posts to channel on failure only
- **Notion**: Every run (success, failure, or skipped) logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run

---

## Margin Utilization Update

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\S3_Data\run-margin-utilization.ps1` |
| Python | `C:\Users\RodrigoGordillo\S3_Data\update_margin_utilization.py --incremental` |
| Wrapper | `C:\Users\RodrigoGordillo\S3_Data\update_margin_utilization.bat` |
| Schedule | Every day at 3:00 AM ET (Windows Task Scheduler) |
| Task name | `S3 Sync - Margin Utilization Update` |
| Description | Appends new daily `margin_to_equity` values from Dropbox metadata files (`futures_{YYYY-MM-DD}.csv`) to `Live_Margin_Utilization.csv`, then incrementally updates ~30 strategy margin utilization Excel files across 12 strategies. Uses hybrid margin approach: static `margin.json` for pre-2020, daily live margins for post-2020. |

### Data Sources

| Source | Path |
|---|---|
| Static margins | `S3_Data\margin.json` |
| Live margins (consolidated) | `S3_Data\backtest-sims-dev\Margin_utilization\Live_Margin_Utilization.csv` |
| Daily margin files (raw) | `ReSolve AM Dropbox\trading_data\futures\metadata\futures_{YYYY-MM-DD}.csv` |
| Portfolio weights | `S3_Data\backtest-sims-dev\portfolio_weights\{mandate}\latest\strategy\` |
| Output | `S3_Data\backtest-sims-dev\Margin_utilization\{Strategy}\margin*.csv` |

### Alerting

- **Slack**: Webhook posts to channel on failure only
- **Notion**: Every run (success or failure) logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run

---

## Source File Sync

| Field | Value |
|---|---|
| Script | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\Notion_Source_File_Sync\notion_source_file_sync.py` |
| Wrapper | `C:\Users\RodrigoGordillo\ReSolve AM Dropbox\Rodrigo Gordillo\RG Documents\RAM_Brain\projects\Notion_Source_File_Sync\run-source-file-sync.bat` |
| Schedule | Every day at 1:00 AM ET (Windows Task Scheduler) |
| Task name | `Source File Sync` |
| Description | Queries the Runs database for entries where "Ready For Approval" = "Approved". Downloads Sources file(s) from approved Runs and re-uploads them to the linked Publications List [M&S] page's "Source files" field via the Notion File Upload API. Tracks processed Run IDs to avoid duplicates. |

### Notion Databases

| Database | ID | Purpose |
|---|---|---|
| Runs | `2f63037cb38a8060908ce6e1ae5aeeeb` | Source database — monitors "Ready For Approval" = "Approved" |
| Publications List [M&S] | `60b55bf954ce476ca050167034bd1346` | Target database — "Source files" field receives uploaded files |
| Automation Runs | `3023037cb38a815fb09fd3d2b6f71ae7` | Run history log (success/failure per run) |
| Automations Inventory | `3023037cb38a814bac81cb56a89af346` | Central inventory of all automations |

### Alerting

- **Slack**: Webhook posts to channel on failure only
- **Notion**: Every run (success or failure) logged to "Automation Runs" DB
- **Notion Inventory**: "Last Run" and "Last Status" updated after each run
